# PLAN
Python implementation for PLAN: A Policy-Aware and Network-Aware VM Management Scheme for Cloud Data Centres. The distributed algorithm is implemented aloneside Xen Hypervisor and uses xl (http://wiki.xen.org/wiki/XL) to interact with it. SDN controller is imployed to support policy implementation/query and keeps flow statistics. 

## Repo Structure
```
-/root
 |- README.md /*this document*/
 |--/src    /*source code for the main distributed decision making algorithms*/
 |--/test   /*source code for testing*/
```

## Prerequisites
* OpenDaylight (with OpenFlow plugin)
* Xen Hypervisor v4.3+
* Open vSwitch

## Publications
* Lin Cui, Fung Po Tso, Dimitrios P. Pezaros, Weijia Jia, Wei Zho, "Policy-Aware Virtual Machine Management in Data Center Networks", in the proceedings of IEEE ICDCS 2015, June 2015, Columbus, USA. 
