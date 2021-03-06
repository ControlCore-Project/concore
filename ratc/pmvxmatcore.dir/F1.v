`timescale 1ns/100ps

module F1 (zh,f1);
input [9:0] zh;
output [14:0] f1;
reg [14:0] f1;

always @ (zh)
case (zh)
0 : f1 = -2335;
1023 : f1 = 0;
1022 : f1 = -2303;
1021 : f1 = -1774;
1020 : f1 = -1459;
1019 : f1 = -1230;
1018 : f1 = -1048;
1017 : f1 = -897;
1016 : f1 = -767;
1015 : f1 = -651;
1014 : f1 = -547;
1013 : f1 = -452;
1012 : f1 = -365;
1011 : f1 = -283;
1010 : f1 = -206;
1009 : f1 = -134;
1008 : f1 = -65;
1007 : f1 = 0;
1006 : f1 = 63;
1005 : f1 = 123;
1004 : f1 = 181;
1003 : f1 = 237;
1002 : f1 = 291;
1001 : f1 = 344;
1000 : f1 = 396;
999 : f1 = 446;
998 : f1 = 495;
997 : f1 = 543;
996 : f1 = 589;
995 : f1 = 635;
994 : f1 = 681;
993 : f1 = 725;
992 : f1 = 769;
991 : f1 = 812;
990 : f1 = 854;
989 : f1 = 896;
988 : f1 = 937;
987 : f1 = 978;
986 : f1 = 1018;
985 : f1 = 1058;
984 : f1 = 1097;
983 : f1 = 1136;
982 : f1 = 1175;
981 : f1 = 1213;
980 : f1 = 1251;
979 : f1 = 1289;
978 : f1 = 1327;
977 : f1 = 1364;
976 : f1 = 1401;
975 : f1 = 1437;
974 : f1 = 1474;
973 : f1 = 1510;
972 : f1 = 1546;
971 : f1 = 1582;
970 : f1 = 1618;
969 : f1 = 1653;
968 : f1 = 1688;
967 : f1 = 1724;
966 : f1 = 1759;
965 : f1 = 1794;
964 : f1 = 1828;
963 : f1 = 1863;
962 : f1 = 1897;
961 : f1 = 1932;
960 : f1 = 1966;
959 : f1 = 2000;
958 : f1 = 2034;
957 : f1 = 2068;
956 : f1 = 2102;
955 : f1 = 2136;
954 : f1 = 2170;
953 : f1 = 2204;
952 : f1 = 2237;
951 : f1 = 2271;
950 : f1 = 2304;
949 : f1 = 2337;
948 : f1 = 2371;
947 : f1 = 2404;
946 : f1 = 2437;
945 : f1 = 2470;
944 : f1 = 2503;
943 : f1 = 2537;
942 : f1 = 2570;
941 : f1 = 2603;
940 : f1 = 2635;
939 : f1 = 2668;
938 : f1 = 2701;
937 : f1 = 2734;
936 : f1 = 2767;
935 : f1 = 2799;
934 : f1 = 2832;
933 : f1 = 2865;
932 : f1 = 2898;
931 : f1 = 2930;
930 : f1 = 2963;
929 : f1 = 2995;
928 : f1 = 3028;
927 : f1 = 3060;
926 : f1 = 3093;
925 : f1 = 3125;
924 : f1 = 3158;
923 : f1 = 3190;
922 : f1 = 3223;
921 : f1 = 3255;
920 : f1 = 3287;
919 : f1 = 3320;
918 : f1 = 3352;
917 : f1 = 3384;
916 : f1 = 3417;
915 : f1 = 3449;
914 : f1 = 3481;
913 : f1 = 3514;
912 : f1 = 3546;
911 : f1 = 3578;
910 : f1 = 3610;
909 : f1 = 3643;
908 : f1 = 3675;
907 : f1 = 3707;
906 : f1 = 3739;
905 : f1 = 3772;
904 : f1 = 3804;
903 : f1 = 3836;
902 : f1 = 3868;
901 : f1 = 3900;
900 : f1 = 3932;
899 : f1 = 3965;
898 : f1 = 3997;
897 : f1 = 4029;
896 : f1 = 4061;
895 : f1 = 4093;
894 : f1 = 4125;
893 : f1 = 4157;
892 : f1 = 4189;
891 : f1 = 4222;
890 : f1 = 4254;
889 : f1 = 4286;
888 : f1 = 4318;
887 : f1 = 4350;
886 : f1 = 4382;
885 : f1 = 4414;
884 : f1 = 4446;
883 : f1 = 4478;
882 : f1 = 4510;
881 : f1 = 4542;
880 : f1 = 4574;
879 : f1 = 4607;
878 : f1 = 4639;
877 : f1 = 4671;
876 : f1 = 4703;
875 : f1 = 4735;
874 : f1 = 4767;
873 : f1 = 4799;
872 : f1 = 4831;
default : f1 = 0;
endcase

endmodule