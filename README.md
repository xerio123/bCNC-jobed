# bCNC-jobed
fork bcnc
 With a tab adding confort for small screen No 3th axis controle on this panel only for 2D axis move
 version used is 0.9.14-dev


to simulate this version of bcnc you can use software proteus (version 8.4 run well for this project) repertory "proteus 8.4" contain the poject to simulate an hardware controleur (with arduino R3) so don't forget if needed to add arduino firmware (right click on arduino > edit propryties) and add: grbl_v0_9i_atmega328p_16mhz_115200.hex
(version 0.9i work well) see img: https://github.com/xerio123/bCNC-jobed/blob/master/proteus%208.4/configarduino.png

to simulate you need also an virtual com port, for that i use port0port at adresse : http://com0com.sourceforge.net/ this is needed to transmit data between bcnc and simulate hardware in proteus (also, don't forget configure the correct port in proteue and bcnc, baudrate is alway 115200)

see config
