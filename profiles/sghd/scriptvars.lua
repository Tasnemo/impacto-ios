-- Round 11: original Steam SCX confirms its background control bank is W4500.
-- In SG00_01.SCX a 10:01 LoadBackground(1,59) is immediately followed
-- by W4508 = 11 (priority); the same scene writes W4511 = 1 and = 15
-- (render modes), and W4500/W4501/W4504 for position/scale.
-- The old inherited SGPS3 overrides redirected those fields to W2400
-- and caused the renderer to treat an increasing W2411 counter as mode
-- 40..180. Inherit the shared/Steam W4500 and W2500 offset bank here.
-- Surface/link address inheritance (W3400/W4490) is still a hypothesis
-- under live validation, not proven solely by those SCX assignments.
-- Original background textures remain local, never in the repository.
-- Thread 07c: the Steam scripts use the common (profiles/common/
-- scriptvars.lua) title/system-menu variables, not the PS3 values this file
-- inherited from sgps3: _STARTUP_WIN counts SW_TITLEDISPCT in W2119, sets
-- SW_TITLEMODE W2115, SW_GAMESTATE W2113, SW_SYSMENUCT/ALPHA W2142/W2143,
-- reads SW_TITLECUR W2139, SW_SYSMENUCNO W3338 and tests W4300 == 65535
-- (SW_TITLE). The PS3 overrides of those were removed; the remaining ones
-- are unverified.
local sv = root.ScriptVars;

sv.SW_TITLEMASKALPHA = 1033;
sv.SW_TITLEMASKCOLOR = 1034;
sv.SW_SYSSEL = 1028;
sv.SW_SYSTEMMENUCHG = 1040;
sv.SW_SYSTEMMENUALPHA = 1041;
sv.SW_MASK1ALPHA_OFS = 1586;
sv.SW_MASK2ALPHA_OFS = 1587;
sv.SW_MASK3ALPHA_OFS = 1588;
sv.SW_MAINTHDP = 1704;
sv.SW_SAVEERRORCODE = 1733;
sv.SW_TITLECUR1 = 1740;
sv.SW_TITLECUR2 = 1741;
sv.SW_SVSENO = 2001;
sv.SW_SVBGMNO = 2005;
sv.SW_SVSCRNO1 = 2006;
sv.SW_SVSCRNO2 = 2007;
sv.SW_SVSCRNO3 = 2008;
sv.SW_SVSCRNO4 = 2009;
sv.SW_SVBGNO1 = 2010;
sv.SW_SVCHANO1 = 2018;
sv.SW_PLAYTIME = 2304;
sv.SW_MESWINDOW_COLOR = 7777;
sv.SW_BGMREQNO = 2310;
sv.SW_SEREQNO = 2311;
sv.SW_BGMVOL = 2314;
sv.SW_SEVOL = 2315;
sv.SW_SCRIPTNO0 = 2320;
sv.SW_SCRIPTNO1 = 2321;
sv.SW_SCRIPTNO2 = 2322;
sv.SW_SCRIPTNO3 = 2323;
sv.SW_SCRIPTNO4 = 2324;
sv.SW_SCRIPTNO5 = 2325;
sv.SW_SCRIPTNO6 = 2326;
sv.SW_SCRIPTNO7 = 2327;
sv.SW_MASK1COLOR = 2329;
sv.SW_MASK1ALPHA = 2330;
sv.SW_MASK1PRI = 2331;
sv.SW_MASK1POSX = 2332;
sv.SW_MASK1POSY = 2333;
sv.SW_MASK1SIZEX = 2334;
sv.SW_MASK1SIZEY = 2335;
sv.SW_MESMODE0 = 3173;
sv.SW_CHA1POSX = 2600;
sv.SW_CHA1POSY = 2601;
sv.SW_CHA1ROTX = 2602;
sv.SW_CHA1ROTY = 2603;
sv.SW_CHA1ROTZ = 2604;
sv.SW_CHA1ALPHA = 2607;
sv.SW_CHA1NO = 2609;
sv.SW_CHA1PRI = 2610;
sv.SW_CHA1POSE = 2611;
sv.SW_CHA1FACE = 2612;
sv.SW_CHA1EX = 2613;
sv.SW_CHA1FADECT = 2614;
sv.SW_CHA1FADETYPE = 2615;
sv.SW_CHA1SURF = 1850;
sv.SW_CHA1POSY_OFS = 1301;
sv.SW_CHA1ALPHA_OFS = 1307;
sv.SW_SAVEFILESTATUS = 2122;
sv.SW_SAVEFILENO = 2123;
sv.SW_EFF_CAP_PRI = 3268;
sv.SW_EFF_CAP_BUF = 3269;
sv.SW_EFF_CAP_PRI2 = 3270;
sv.SW_EFF_CAP_BUF2 = 3271;