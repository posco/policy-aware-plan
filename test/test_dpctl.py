import add_to_sys_path
import dpctl
import unittest

class TestFlowEntry(unittest.TestCase):
	""" Test the basic FlowEntry class. """

	def test_init(self):
		""" This is probably quite a pointless test case. """
		entry = dpctl.FlowEntry('00:00:00:00:00:01', '00:00:00:00:00:02',
								'10.0.0.1', '10.0.0.2', 0)
		self.assertEqual(entry.srcMac, '00:00:00:00:00:01')
		self.assertTrue(entry.dstMac == '00:00:00:00:00:02')
		self.assertTrue(entry.srcIp == '10.0.0.1')
		self.assertTrue(entry.dstIp == '10.0.0.2')
		self.assertTrue(entry.bytes == 0)


class TestFlowsInitialisation(unittest.TestCase):
	""" Test flows are correctly initialised and our accessors return what is expected. """

	def setUp(self):
		self.flows = dpctl.Flows()
		self.dict = dict()

	def test_src_flows(self):
		""" Make sure src flows are empty. """
		self.assertEqual(self.flows._src, self.dict)

	def test_dst_flows(self):
		""" Make sure dst flows are empty. """
		self.assertEqual(self.flows._dst, self.dict)

class TestFlowsAdd(unittest.TestCase):
	""" Test that new flow entries are correctly added. """
	
	def setUp(self):
		self.flows = dpctl.Flows()
		self.entry = dpctl.FlowEntry('00:00:00:00:00:01', '00:00:00:00:00:02',
						  '192.168.1.1', '192.168.1.2', 96)

	def test_add_src_flow(self):
		self.flows.add_new_src_flow(self.entry)
		srcIp = self.entry.srcIp
		srcMac = self.entry.srcMac
		dstIp = self.entry.dstIp
		bytes = self.entry.bytes
		date = self.flows._src[srcIp][2]
		self.assertTrue(self.flows._src.has_key(srcIp))
		self.assertEquals(self.flows._src[srcIp], [srcMac, {dstIp: [bytes, 0]}, date])

	def test_add_dst_flow(self):
		self.flows.add_new_dst_flow(self.entry)
		srcIp = self.entry.srcIp
		dstMac = self.entry.dstMac
		dstIp = self.entry.dstIp
		bytes = self.entry.bytes
		date = self.flows._dst[dstIp][2]
		self.assertTrue(self.flows._dst.has_key(dstIp))
		self.assertEquals(self.flows._dst[dstIp], [dstMac, {srcIp: [bytes, 0]}, date])

class TestFlowsHasEntry(unittest.TestCase):
	""" Test that flow entry lookups return expected results. """

	def setUp(self):
		self.flows = dpctl.Flows()
		self.entry = dpctl.FlowEntry('00:00:00:00:00:01', '00:00:00:00:00:02',
						  '192.168.1.1', '192.168.1.2', 96)

	def test_has_src_flow(self):
		self.flows.add_new_src_flow(self.entry)
		srcIp = self.entry.srcIp
		self.assertTrue(self.flows.has_src_flow_history(srcIp))

	def test_has_src_flow_not_match_dst(self):
		self.flows.add_new_src_flow(self.entry)
		srcIp = self.entry.srcIp
		self.assertFalse(self.flows.has_dst_flow_history(srcIp))

	def test_has_dst_flow(self):
		self.flows.add_new_dst_flow(self.entry)
		dstIp = self.entry.dstIp
		self.assertTrue(self.flows.has_dst_flow_history(dstIp))

	def test_has_dst_flow_not_match_src(self):
		self.flows.add_new_dst_flow(self.entry)
		dstIp = self.entry.dstIp
		self.assertFalse(self.flows.has_src_flow_history(dstIp))

class TestFlowsIncrement(unittest.TestCase):
	""" Test incrementing byte values in existing flow entries. """

	def setUp(self):
		self.flows = dpctl.Flows()
		self.entry = dpctl.FlowEntry('00:00:00:00:00:01', '00:00:00:00:00:02',
						  '192.168.1.1', '192.168.1.2', 96)

	def test_increment_src_flow_none_existing(self):
		self.flows.increment_src_flow(self.entry)
		self.assertEqual(self.flows._src, dict())

	def test_increment_src_flow_one_existing(self):
		self.flows.add_new_src_flow(self.entry)
		self.entry.bytes = self.entry.bytes * 2
		self.flows.increment_src_flow(self.entry)
		srcIp = self.entry.srcIp
		dstMac = self.entry.dstMac
		dstIp = self.entry.dstIp
		bytes = self.entry.bytes
		self.assertEquals(self.flows._src[srcIp][1][dstIp][0], bytes)

	def test_increment_src_flow_new_start(self):
		self.flows.add_new_src_flow(self.entry)
		self.entry.bytes = 48
		self.flows.increment_src_flow(self.entry)
		srcIp = self.entry.srcIp
		dstMac = self.entry.dstMac
		dstIp = self.entry.dstIp
		bytes = self.entry.bytes
		self.assertEquals(self.flows._src[srcIp][1][dstIp][0], 48)
		self.assertEquals(self.flows._src[srcIp][1][dstIp][1], 96)

	def test_increment_src_flow_new_start_and_increment(self):
		self.flows.add_new_src_flow(self.entry)
		self.entry.bytes = 48
		self.flows.increment_src_flow(self.entry)
		self.entry.bytes = 128
		self.flows.increment_src_flow(self.entry)
		srcIp = self.entry.srcIp
		dstMac = self.entry.dstMac
		dstIp = self.entry.dstIp
		bytes = self.entry.bytes
		self.assertEquals(self.flows._src[srcIp][1][dstIp][0], 128)
		self.assertEquals(self.flows._src[srcIp][1][dstIp][1], 96)

class TestFlowsUpdate(unittest.TestCase):
	""" Test the decision methods that choose whether to add/increment flows. """

	def setUp(self):
		self.flows = dpctl.Flows()
		self.entry = dpctl.FlowEntry('00:00:00:00:00:01', '00:00:00:00:00:02',
						  '192.168.1.1', '192.168.1.2', 96)

	def test_update_src_flow_add(self):
		self.flows.update_src_flow(self.entry)
		srcIp = self.entry.srcIp
		srcMac = self.entry.srcMac
		dstIp = self.entry.dstIp
		bytes = self.entry.bytes
		date = self.flows._src[srcIp][2]
		self.assertTrue(self.flows._src.has_key(srcIp))
		self.assertEquals(self.flows._src[srcIp], [srcMac, {dstIp: [bytes, 0]}, date])

	def test_update_src_flow_increment(self):
		self.flows.update_src_flow(self.entry)
		self.entry.bytes = 128
		self.flows.update_src_flow(self.entry)
		srcIp = self.entry.srcIp
		srcMac = self.entry.srcMac
		dstIp = self.entry.dstIp
		bytes = self.entry.bytes
		date = self.flows._src[srcIp][2]
		self.assertTrue(self.flows._src.has_key(srcIp))
		self.assertEquals(self.flows._src[srcIp], [srcMac, {dstIp: [bytes, 0]}, date])

	def test_update_src_flow_new_start(self):
		self.flows.update_src_flow(self.entry)
		self.entry.bytes = 48
		self.flows.update_src_flow(self.entry)
		srcIp = self.entry.srcIp
		srcMac = self.entry.srcMac
		dstIp = self.entry.dstIp
		bytes = self.entry.bytes
		date = self.flows._src[srcIp][2]
		self.assertTrue(self.flows._src.has_key(srcIp))
		self.assertEquals(self.flows._src[srcIp], [srcMac, {dstIp: [bytes, 96]}, date])

	def test_update_src_flow_new_dst(self):
		self.flows.update_src_flow(self.entry)
		oldDstIp = self.entry.dstIp
		self.entry.dstMac = '00:00:00:00:00:03'
		self.entry.dstIp = '192.168.1.3'
		self.flows.update_src_flow(self.entry)
		srcIp = self.entry.srcIp
		srcMac = self.entry.srcMac
		dstIp = self.entry.dstIp
		bytes = self.entry.bytes
		date = self.flows._src[srcIp][2]
		self.assertTrue(self.flows._src.has_key(srcIp))
		self.assertEquals(self.flows._src[srcIp], [srcMac, {oldDstIp: [bytes, 0], dstIp: [bytes, 0]}, date])

	def test_update_src_flow_new_flow(self):
		self.flows.update_src_flow(self.entry)
		oldSrcMac = self.entry.srcMac
		oldSrcIp = self.entry.srcIp
		oldDstIp = self.entry.dstIp
		oldDate = self.flows._src[self.entry.srcIp][2]
		self.entry.srcMac = '00:00:00:00:00:04'
		self.entry.srcIp = '192.168.1.4'
		self.entry.dstMac = '00:00:00:00:00:03'
		self.entry.dstIp = '192.168.1.3'
		self.flows.update_src_flow(self.entry)
		srcIp = self.entry.srcIp
		srcMac = self.entry.srcMac
		dstIp = self.entry.dstIp
		bytes = self.entry.bytes
		date = self.flows._src[srcIp][2]
		self.assertTrue(self.flows._src.has_key(srcIp))
		self.assertEquals(self.flows._src[oldSrcIp], [oldSrcMac, {oldDstIp: [bytes, 0]}, oldDate])
		self.assertEquals(self.flows._src[srcIp], [srcMac, {dstIp: [bytes, 0]}, date])

class TestFlowsReset(unittest.TestCase):
	""" Test the ability to reset byte counters for individual flows. """

	def setUp(self):
		self.flows = dpctl.Flows()
		self.entry = dpctl.FlowEntry('00:00:00:00:00:01', '00:00:00:00:00:02',
						  '192.168.1.1', '192.168.1.2', 96)

	def test_reset_src_flows(self):
		self.flows.update_src_flow(self.entry)
		self.flows.reset_src_flows('192.168.1.1')
		srcIp = self.entry.srcIp
		srcMac = self.entry.srcMac
		dstIp = self.entry.dstIp
		date = self.flows._src[srcIp][2]
		self.assertEquals(self.flows._src[srcIp], [srcMac, {dstIp: [96, -96]}, date])

	def test_reset_src_flows_update_same(self):
		self.flows.update_src_flow(self.entry)
		self.flows.reset_src_flows('192.168.1.1')
		self.entry.bytes = 96
		self.flows.update_src_flow(self.entry)
		srcIp = self.entry.srcIp
		srcMac = self.entry.srcMac
		dstIp = self.entry.dstIp
		date = self.flows._src[srcIp][2]
		self.assertEquals(self.flows._src[srcIp], [srcMac, {dstIp: [96, -96]}, date])

	def test_reset_src_flows_update(self):
		self.flows.update_src_flow(self.entry)
		self.flows.reset_src_flows('192.168.1.1')
		self.entry.bytes = 128
		self.flows.update_src_flow(self.entry)
		srcIp = self.entry.srcIp
		srcMac = self.entry.srcMac
		dstIp = self.entry.dstIp
		date = self.flows._src[srcIp][2]
		self.assertEquals(self.flows._src[srcIp], [srcMac, {dstIp: [128, -96]}, date])

	def test_reset_src_flows_update_new_start(self):
		self.flows.update_src_flow(self.entry)
		self.flows.reset_src_flows('192.168.1.1')
		self.entry.bytes = 48
		self.flows.update_src_flow(self.entry)
		srcIp = self.entry.srcIp
		srcMac = self.entry.srcMac
		dstIp = self.entry.dstIp
		date = self.flows._src[srcIp][2]
		self.assertEquals(self.flows._src[srcIp], [srcMac, {dstIp: [48, 0]}, date])

class TestFlowsGet(unittest.TestCase):
		""" Test the ability to retrieve flows references (without copying). """

class TestFlowsCopy(unittest.TestCase):
		""" Test the ability to deep copy flows. """

class TestFlowsGetMac(unittest.TestCase):
		""" Test the ability to retrieve MACs from flow mappings. """

if (__name__ == '__main__'):
	unittest.main()

