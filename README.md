# PLAN
Python implementation for PLAN: A Policy-Aware and Network-Aware VM Management Scheme for Cloud Data Centres. The distributed algorithm is implemented aloneside Xen Hypervisor and uses xm to interact with it. Please note that this repo only contains distributed algorithms and policy query from a policy controller (SDN controller). Source for more sophiticated SDN orchestration including flow monitoring and statistics, link cost assignment etc is available at https://github.com/simon-jouet/sdnscore

## Repo Structure
```
-/root
 |- README.md /*this document*/
 |--/src    /*source code for the main distributed decision making algorithms*/
 |--/test   /*source code for testing*/
```

## Prerequisites
* OpenDaylight (with OpenFlow plugin) or Ryu SDN Framework 
* Xen Hypervisor v4.2+
* Open vSwitch
* SDN S-CORE (https://github.com/simon-jouet/sdnscore)

## Publications
* Lin Cui, Fung Po Tso, Dimitrios P. Pezaros, Weijia Jia, Wei Zho, "Policy-Aware Virtual Machine Management in Data Center Networks", in the proceedings of IEEE ICDCS 2015, June 2015, Columbus, USA. 
