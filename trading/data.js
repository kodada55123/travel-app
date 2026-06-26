// ═══════════════════════════════════════════════════════════════
// data.js  ──  每日更新此檔案即可，勿修改 index.html 的邏輯
// ═══════════════════════════════════════════════════════════════
const LAST_UPDATED = "2026-06-25";

// ── 未實現持倉（每次更新此區塊）─────────────────────────────────
const POSITIONS = [
  { stock:"富邦台50",    code:"006208", type:"ETF",  shares:11000, avgCost:99.23,   price:248.1,  value:2725367, pnl:1633467, pct:149.60 },
  { stock:"國泰永續高股息",code:"00878", type:"ETF",  shares:31000, avgCost:22.01,   price:33.75,  value:1044811, pnl:362329,  pct:53.09  },
  { stock:"元大台灣50",  code:"0050",   type:"ETF",  shares:8000,  avgCost:61.76,   price:107.2,  value:856415,  pnl:362151,  pct:73.27  },
  { stock:"群益台灣精選高息",code:"00919",type:"ETF", shares:6000,  avgCost:22.57,   price:30.26,  value:181308,  pnl:45866,   pct:33.86  },
  { stock:"復華富時不動產",code:"00712", type:"ETF",  shares:12000, avgCost:9.61,    price:8.6,    value:103063,  pnl:-12342,  pct:-10.69 },
  { stock:"富鼎",        code:"8261",   type:"股票", shares:1000,  avgCost:173.0,   price:255.5,  value:254633,  pnl:81564,   pct:47.13  },
  { stock:"力智",        code:"6719",   type:"股票", shares:1000,  avgCost:278.0,   price:295.5,  value:294497,  pnl:16387,   pct:5.89   },
  { stock:"順德",        code:"2351",   type:"股票", shares:1300,  avgCost:196.96,  price:209.0,  value:270780,  pnl:14628,   pct:5.71   },
  { stock:"群聯",        code:"8299",   type:"股票", shares:80,    avgCost:2463.13, price:2475.0, value:197332,  pnl:206,     pct:0.10   },
  { stock:"博智",        code:"8155",   type:"股票", shares:300,   avgCost:404.42,  price:391.5,  value:117056,  pnl:-4317,   pct:-3.56  },
];

// ── 已實現損益摘要（每次出清一筆時新增）──────────────────────────
const REALIZED = [
  { stock:"富邦台50",    buyDate:"—",        sellDate:"持有中", cost:0,       proceeds:0,      pnl:1633467, pct:149.60, note:"前期長線持有" },
  { stock:"世芯-KY",    buyDate:"前期",      sellDate:"2026-01-29", cost:0,   proceeds:172590, pnl:172590,  pct:0,      note:"前期持有出清" },
  { stock:"達麗",       buyDate:"前期",      sellDate:"2026-01-02", cost:0,   proceeds:157366, pnl:157366,  pct:0,      note:"前期持有出清" },
  { stock:"聯發科",     buyDate:"2026-04-14",sellDate:"2026-06-08", cost:69200,proceeds:167300,pnl:98100,   pct:141.76, note:"長波段，計畫完整" },
  { stock:"貿聯-KY",    buyDate:"2026-01-12",sellDate:"2026-05-06", cost:312518,proceeds:367453,pnl:54935,  pct:17.6,   note:"多批次進出" },
  { stock:"奇鋐（第一段）",buyDate:"2026-01-08",sellDate:"2026-04-09",cost:190800,proceeds:261600,pnl:70800,pct:37.1,  note:"分批出場，紀律良好" },
  { stock:"毅嘉",       buyDate:"2026-04-09",sellDate:"2026-04-16", cost:56322,proceeds:67272, pnl:10950,   pct:19.4,   note:"快進快出" },
  { stock:"臺慶科",     buyDate:"2026-06-05",sellDate:"2026-06-12", cost:348500,proceeds:358500,pnl:8462,   pct:2.43,   note:"爆量入場，規則完整" },
  { stock:"頎邦",       buyDate:"2026-03-16",sellDate:"2026-03-17", cost:60023,proceeds:63185, pnl:3162,    pct:5.3,    note:"隔日沖" },
  { stock:"今展科",     buyDate:"2026-06-10",sellDate:"2026-06-23", cost:153361,proceeds:157465,pnl:4104,   pct:2.7,    note:"小獲利" },
  { stock:"中興電",     buyDate:"2026-01-14",sellDate:"2026-01-19", cost:78531,proceeds:79978, pnl:1447,    pct:1.8,    note:"短進短出" },
  { stock:"達欣工",     buyDate:"2026-04-29",sellDate:"2026-04-30", cost:74829,proceeds:74945, pnl:116,     pct:0.2,    note:"小獲利" },
  { stock:"緯創",       buyDate:"2026-05-22",sellDate:"2026-06-11", cost:321500,proceeds:307000,pnl:-14500, pct:-4.51,  note:"恐慌加碼，擴大虧損" },
  { stock:"奇鋐（第二段）",buyDate:"2026-06-03",sellDate:"2026-06-04",cost:203700,proceeds:190600,pnl:-13100,pct:-6.4, note:"興奮情緒開倉" },
  { stock:"鈺創",       buyDate:"2026-05-06",sellDate:"2026-05-08", cost:177470,proceeds:168507,pnl:-8963,  pct:-5.1,   note:"3天快輸" },
  { stock:"雙鴻",       buyDate:"2026-06-01",sellDate:"2026-06-05", cost:207000,proceeds:197929,pnl:-7927,  pct:-3.83,  note:"停損執行正確" },
  { stock:"迅得",       buyDate:"2026-03-17",sellDate:"2026-03-18", cost:64225,proceeds:61990, pnl:-2235,   pct:-3.5,   note:"隔日停損" },
  { stock:"智邦",       buyDate:"2026-01-27",sellDate:"2026-01-30", cost:58773,proceeds:57306, pnl:-1467,   pct:-2.5,   note:"短線小虧" },
];

// ── 交易明細（從對帳單匯入，action: BUY/SELL）────────────────────
const TRADES = [
  // 2026-06-23
  { date:"2026-06-23", stock:"順德",   action:"BUY",  price:201.5, shares:100,  net:-20158,  fee:8,  tax:0,   note:"" },
  { date:"2026-06-23", stock:"順德",   action:"BUY",  price:202,   shares:100,  net:-20208,  fee:8,  tax:0,   note:"" },
  { date:"2026-06-23", stock:"順德",   action:"BUY",  price:202,   shares:100,  net:-20208,  fee:8,  tax:0,   note:"" },
  { date:"2026-06-23", stock:"今展科", action:"SELL", price:76.3,  shares:1000, net:76042,   fee:30, tax:228, note:"" },
  { date:"2026-06-23", stock:"力智",   action:"BUY",  price:278,   shares:1000, net:-278110, fee:110,tax:0,   note:"" },
  { date:"2026-06-23", stock:"博智",   action:"SELL", price:388.5, shares:200,  net:77436,   fee:31, tax:233, note:"" },
  // 2026-06-22
  { date:"2026-06-22", stock:"今展科", action:"SELL", price:81.7,  shares:1000, net:81423,   fee:32, tax:245, note:"" },
  // 2026-06-18
  { date:"2026-06-18", stock:"順德",   action:"BUY",  price:195.5, shares:1000, net:-195578, fee:78, tax:0,   note:"" },
  { date:"2026-06-18", stock:"界霖",   action:"SELL", price:93.1,  shares:1000, net:92784,   fee:37, tax:279, note:"" },
  { date:"2026-06-18", stock:"群聯",   action:"BUY",  price:2455,  shares:20,   net:-49119,  fee:19, tax:0,   note:"" },
  { date:"2026-06-18", stock:"群聯",   action:"BUY",  price:2460,  shares:10,   net:-24609,  fee:9,  tax:0,   note:"" },
  { date:"2026-06-18", stock:"群聯",   action:"BUY",  price:2475,  shares:30,   net:-74279,  fee:29, tax:0,   note:"" },
  { date:"2026-06-18", stock:"群聯",   action:"BUY",  price:2455,  shares:20,   net:-49119,  fee:19, tax:0,   note:"" },
  // 2026-06-17
  { date:"2026-06-17", stock:"博智",   action:"BUY",  price:404.5, shares:100,  net:-40466,  fee:16, tax:0,   note:"" },
  // 2026-06-16
  { date:"2026-06-16", stock:"力積電", action:"SELL", price:73.6,  shares:1000, net:73351,   fee:29, tax:220, note:"" },
  { date:"2026-06-16", stock:"力積電", action:"SELL", price:73.4,  shares:1000, net:73151,   fee:29, tax:220, note:"" },
  { date:"2026-06-16", stock:"博智",   action:"BUY",  price:400,   shares:26,   net:-10404,  fee:4,  tax:0,   note:"" },
  { date:"2026-06-16", stock:"博智",   action:"BUY",  price:400,   shares:4,    net:-1601,   fee:1,  tax:0,   note:"" },
  { date:"2026-06-16", stock:"博智",   action:"BUY",  price:400,   shares:87,   net:-34813,  fee:13, tax:0,   note:"" },
  { date:"2026-06-16", stock:"博智",   action:"BUY",  price:406.5, shares:33,   net:-13419,  fee:5,  tax:0,   note:"" },
  { date:"2026-06-16", stock:"博智",   action:"BUY",  price:406,   shares:100,  net:-40616,  fee:16, tax:0,   note:"" },
  { date:"2026-06-16", stock:"博智",   action:"BUY",  price:403.5, shares:50,   net:-20183,  fee:8,  tax:0,   note:"" },
  { date:"2026-06-16", stock:"博智",   action:"BUY",  price:404,   shares:100,  net:-40416,  fee:16, tax:0,   note:"" },
  // 2026-06-15
  { date:"2026-06-15", stock:"界霖",   action:"BUY",  price:92.7,  shares:1000, net:-92736,  fee:36, tax:0,   note:"" },
  { date:"2026-06-15", stock:"界霖",   action:"SELL", price:90.8,  shares:1000, net:90628,   fee:36, tax:136, note:"" },
  { date:"2026-06-15", stock:"界霖",   action:"BUY",  price:92.5,  shares:1000, net:-92536,  fee:36, tax:0,   note:"" },
  { date:"2026-06-15", stock:"界霖",   action:"BUY",  price:92.5,  shares:1000, net:-92536,  fee:36, tax:0,   note:"" },
  { date:"2026-06-15", stock:"界霖",   action:"SELL", price:88.1,  shares:1000, net:87933,   fee:35, tax:132, note:"" },
  // 2026-06-12
  { date:"2026-06-12", stock:"臺慶科", action:"SELL", price:298.5, shares:1000, net:297486,  fee:119,tax:895, note:"出清，+2.43%" },
  { date:"2026-06-12", stock:"富鼎",   action:"BUY",  price:173,   shares:1000, net:-173069, fee:69, tax:0,   note:"" },
  // 2026-06-11
  { date:"2026-06-11", stock:"緯創",   action:"SELL", price:153,   shares:999,  net:152329,  fee:60, tax:458, note:"" },
  { date:"2026-06-11", stock:"緯創",   action:"SELL", price:153.5, shares:1,    net:152,     fee:1,  tax:0,   note:"" },
  { date:"2026-06-11", stock:"緯創",   action:"SELL", price:153,   shares:999,  net:152329,  fee:60, tax:458, note:"" },
  { date:"2026-06-11", stock:"緯創",   action:"SELL", price:153.5, shares:1,    net:152,     fee:1,  tax:0,   note:"" },
  { date:"2026-06-11", stock:"今展科", action:"BUY",  price:75.5,  shares:1000, net:-75530,  fee:30, tax:0,   note:"" },
  // 2026-06-10
  { date:"2026-06-10", stock:"鈊象",   action:"SELL", price:798,   shares:280,  net:222681,  fee:89, tax:670, note:"+0.87%" },
  { date:"2026-06-10", stock:"臺慶科", action:"SELL", price:300,   shares:200,  net:59797,   fee:23, tax:180, note:"部分獲利了結" },
  { date:"2026-06-10", stock:"今展科", action:"BUY",  price:77.8,  shares:1000, net:-77831,  fee:31, tax:0,   note:"" },
  // 2026-06-08
  { date:"2026-06-08", stock:"聯發科", action:"SELL", price:4070,  shares:20,   net:81124,   fee:32, tax:244, note:"無回補全部停利" },
  { date:"2026-06-08", stock:"鈊象",   action:"BUY",  price:783,   shares:30,   net:-23499,  fee:9,  tax:0,   note:"" },
  { date:"2026-06-08", stock:"臺慶科", action:"BUY",  price:286.5, shares:100,  net:-28661,  fee:11, tax:0,   note:"大盤大跌有支撐加碼" },
  { date:"2026-06-08", stock:"臺慶科", action:"BUY",  price:283.5, shares:100,  net:-28361,  fee:11, tax:0,   note:"" },
  // 2026-06-05
  { date:"2026-06-05", stock:"聯發科", action:"SELL", price:4295,  shares:20,   net:85609,   fee:34, tax:257, note:"跌破十日線停利一半" },
  { date:"2026-06-05", stock:"緯創",   action:"BUY",  price:173.5, shares:500,  net:-86784,  fee:34, tax:0,   note:"盤中長上影線量縮加碼（恐慌）" },
  { date:"2026-06-05", stock:"雙鴻",   action:"SELL", price:1095,  shares:100,  net:109129,  fee:43, tax:328, note:"出清，-3.83%" },
  { date:"2026-06-05", stock:"雙鴻",   action:"SELL", price:1110,  shares:40,   net:44250,   fee:17, tax:133, note:"" },
  { date:"2026-06-05", stock:"臺慶科", action:"BUY",  price:291.5, shares:1000, net:-291616, fee:116,tax:0,   note:"底部爆量，大盤大跌個股大漲" },
  // 2026-06-04
  { date:"2026-06-04", stock:"奇鋐",   action:"SELL", price:2725,  shares:40,   net:108630,  fee:43, tax:327, note:"跌破停損，-5.96%" },
  { date:"2026-06-04", stock:"奇鋐",   action:"SELL", price:2720,  shares:30,   net:81324,   fee:32, tax:244, note:"" },
  { date:"2026-06-04", stock:"緯創",   action:"BUY",  price:179.5, shares:500,  net:-89785,  fee:35, tax:0,   note:"回落5日線，量縮加碼" },
  // 2026-06-03 (奇鋐買進 未在對帳單，依日誌補入)
  { date:"2026-06-03", stock:"奇鋐",   action:"BUY",  price:2930,  shares:50,   net:-146610, fee:110,tax:0,   note:"開盤爆大量，情緒盤" },
  { date:"2026-06-03", stock:"奇鋐",   action:"BUY",  price:2860,  shares:20,   net:-57234,  fee:34, tax:0,   note:"" },
  // 2026-06-02
  { date:"2026-06-02", stock:"鈊象",   action:"BUY",  price:792,   shares:20,   net:-15847,  fee:7,  tax:0,   note:"突破上緣，OBV向上" },
  { date:"2026-06-02", stock:"鈊象",   action:"BUY",  price:793,   shares:90,   net:-71397,  fee:27, tax:0,   note:"" },
  { date:"2026-06-02", stock:"鈊象",   action:"BUY",  price:795,   shares:30,   net:-23877,  fee:9,  tax:0,   note:"" },
  { date:"2026-06-02", stock:"雙鴻",   action:"SELL", price:1150,  shares:50,   net:57451,   fee:23, tax:172, note:"帶量買盤無力，減碼" },
  // 2026-06-01
  { date:"2026-06-01", stock:"雙鴻",   action:"BUY",  price:1140,  shares:150,  net:-171068, fee:68, tax:0,   note:"底部帶量突破" },
  { date:"2026-06-03", stock:"鈊象",   action:"BUY",  price:793,   shares:50,   net:-39697,  fee:15, tax:0,   note:"大戶持續吃籌碼" },
  // 2026-05-29
  { date:"2026-05-29", stock:"明泰",   action:"BUY",  price:38.65, shares:1000, net:-38688,  fee:38, tax:0,   note:"帶量突破盤整，法人持續買" },
  { date:"2026-05-29", stock:"明泰",   action:"BUY",  price:38.55, shares:2000, net:-77177,  fee:77, tax:0,   note:"" },
  // 2026-05-28
  { date:"2026-05-28", stock:"光寶科", action:"SELL", price:231.5, shares:1000, net:231269,  fee:92, tax:694, note:"趨勢帶量向下跌破出場，恐慌" },
  { date:"2026-05-28", stock:"光寶科", action:"SELL", price:233,   shares:400,  net:93104,   fee:37, tax:279, note:"" },
  // 2026-05-27
  { date:"2026-05-27", stock:"光寶科", action:"BUY",  price:244.5, shares:200,  net:-48933,  fee:33, tax:0,   note:"帶量上漲趨勢加碼" },
  // 2026-05-26
  { date:"2026-05-26", stock:"光寶科", action:"BUY",  price:238,   shares:200,  net:-47647,  fee:47, tax:0,   note:"帶量上漲趨勢加碼" },
  { date:"2026-05-26", stock:"光寶科", action:"SELL", price:4740,  shares:10,   net:47349,   fee:19, tax:142, note:"跌破區間下緣3%停損（世芯）" },
  { date:"2026-05-26", stock:"光寶科", action:"SELL", price:4755,  shares:5,    net:23737,   fee:9,  tax:71,  note:"出清" },
  // 2026-05-25
  { date:"2026-05-25", stock:"光寶科", action:"SELL", price:4975,  shares:10,   net:49712,   fee:20, tax:149, note:"大盤大漲個股跌，部分停利" },
  // 2026-05-22
  { date:"2026-05-22", stock:"緯創",   action:"BUY",  price:145,   shares:1000, net:-145145, fee:145,tax:0,   note:"帶量突破，OBV向上，偏興奮" },
  // 2026-05-21
  { date:"2026-05-21", stock:"光寶科", action:"BUY",  price:205,   shares:1000, net:-205082, fee:82, tax:0,   note:"偏賭博，無計畫" },
  // 2026-05-13
  { date:"2026-05-13", stock:"AES-KY", action:"BUY",  price:1275,  shares:10,   net:-12755,  fee:5,  tax:0,   note:"" },
  // 2026-05-12
  { date:"2026-05-12", stock:"光寶科", action:"SELL", price:231.5, shares:200,  net:46144,   fee:18, tax:138, note:"" },
  { date:"2026-05-12", stock:"鴻海",   action:"SELL", price:246.5, shares:100,  net:24568,   fee:9,  tax:73,  note:"" },
  { date:"2026-05-12", stock:"AES-KY", action:"BUY",  price:1310,  shares:10,   net:-13105,  fee:5,  tax:0,   note:"" },
  { date:"2026-05-12", stock:"AES-KY", action:"BUY",  price:1295,  shares:10,   net:-12955,  fee:5,  tax:0,   note:"" },
  // 2026-05-08
  { date:"2026-05-08", stock:"光寶科", action:"BUY",  price:205.5, shares:200,  net:-41116,  fee:16, tax:0,   note:"" },
  { date:"2026-05-08", stock:"鴻海",   action:"BUY",  price:249,   shares:200,  net:-49819,  fee:19, tax:0,   note:"" },
  { date:"2026-05-08", stock:"鈺創",   action:"SELL", price:74.4,  shares:1000, net:74148,   fee:29, tax:223, note:"" },
  { date:"2026-05-08", stock:"AES-KY", action:"BUY",  price:1250,  shares:40,   net:-50019,  fee:19, tax:0,   note:"" },
  // 2026-05-07
  { date:"2026-05-07", stock:"創意",   action:"SELL", price:5450,  shares:10,   net:54316,   fee:21, tax:163, note:"" },
  { date:"2026-05-07", stock:"鈺創",   action:"SELL", price:75.8,  shares:200,  net:15109,   fee:6,  tax:45,  note:"" },
  // 2026-05-06
  { date:"2026-05-06", stock:"光寶科", action:"BUY",  price:181.5, shares:400,  net:-72628,  fee:28, tax:0,   note:"" },
  { date:"2026-05-06", stock:"鴻海",   action:"BUY",  price:246.5, shares:100,  net:-24659,  fee:9,  tax:0,   note:"" },
  { date:"2026-05-06", stock:"鴻海",   action:"BUY",  price:246,   shares:100,  net:-24609,  fee:9,  tax:0,   note:"" },
  { date:"2026-05-06", stock:"鴻海",   action:"BUY",  price:245.5, shares:100,  net:-24559,  fee:9,  tax:0,   note:"" },
  { date:"2026-05-06", stock:"鴻海",   action:"BUY",  price:245,   shares:100,  net:-24509,  fee:9,  tax:0,   note:"" },
  { date:"2026-05-06", stock:"貿聯-KY",action:"SELL", price:2705,  shares:15,   net:40438,   fee:16, tax:121, note:"" },
  { date:"2026-05-06", stock:"貿聯-KY",action:"SELL", price:2640,  shares:20,   net:52621,   fee:21, tax:158, note:"" },
  { date:"2026-05-06", stock:"鈺創",   action:"BUY",  price:81,    shares:1000, net:-81032,  fee:32, tax:0,   note:"" },
  { date:"2026-05-06", stock:"鈺創",   action:"SELL", price:79.4,  shares:1000, net:79250,   fee:31, tax:119, note:"" },
  { date:"2026-05-06", stock:"鈺創",   action:"BUY",  price:80.4,  shares:1000, net:-80432,  fee:32, tax:0,   note:"" },
  { date:"2026-05-06", stock:"鈺創",   action:"BUY",  price:80,    shares:200,  net:-16006,  fee:6,  tax:0,   note:"" },
  // 2026-04-30
  { date:"2026-04-30", stock:"光寶科", action:"BUY",  price:173.5, shares:239,  net:-41482,  fee:16, tax:0,   note:"" },
  { date:"2026-04-30", stock:"光寶科", action:"BUY",  price:173,   shares:61,   net:-10557,  fee:4,  tax:0,   note:"" },
  { date:"2026-04-30", stock:"光寶科", action:"BUY",  price:172,   shares:200,  net:-34413,  fee:13, tax:0,   note:"" },
  { date:"2026-04-30", stock:"光寶科", action:"BUY",  price:168,   shares:100,  net:-16806,  fee:6,  tax:0,   note:"" },
  { date:"2026-04-30", stock:"達欣工", action:"SELL", price:75.2,  shares:1000, net:74945,   fee:30, tax:225, note:"+0.2%" },
  { date:"2026-04-30", stock:"貿聯-KY",action:"SELL", price:2755,  shares:5,    net:13729,   fee:5,  tax:41,  note:"" },
  { date:"2026-04-30", stock:"新盛力", action:"SELL", price:155.5, shares:1000, net:154972,  fee:62, tax:466, note:"" },
  { date:"2026-04-30", stock:"新盛力", action:"SELL", price:156.5, shares:250,  net:38993,   fee:15, tax:117, note:"" },
  { date:"2026-04-30", stock:"群聯",   action:"SELL", price:1925,  shares:10,   net:19186,   fee:7,  tax:57,  note:"" },
  // 2026-04-29
  { date:"2026-04-29", stock:"達欣工", action:"BUY",  price:74.8,  shares:1000, net:-74829,  fee:29, tax:0,   note:"" },
  { date:"2026-04-29", stock:"新盛力", action:"SELL", price:158.5, shares:50,   net:7899,    fee:3,  tax:23,  note:"" },
  { date:"2026-04-29", stock:"AES-KY", action:"SELL", price:1155,  shares:20,   net:23022,   fee:9,  tax:69,  note:"" },
  { date:"2026-04-29", stock:"AES-KY", action:"SELL", price:1155,  shares:20,   net:23022,   fee:9,  tax:69,  note:"" },
  { date:"2026-04-29", stock:"AES-KY", action:"SELL", price:1145,  shares:20,   net:22823,   fee:9,  tax:68,  note:"" },
  // 2026-04-28
  { date:"2026-04-28", stock:"群聯",   action:"BUY",  price:1935,  shares:20,   net:-38715,  fee:15, tax:0,   note:"" },
  // 2026-04-27
  { date:"2026-04-27", stock:"新盛力", action:"SELL", price:153,   shares:300,  net:45745,   fee:18, tax:137, note:"" },
  { date:"2026-04-27", stock:"AES-KY", action:"BUY",  price:1210,  shares:60,   net:-72628,  fee:28, tax:0,   note:"" },
  { date:"2026-04-27", stock:"群聯",   action:"BUY",  price:1830,  shares:10,   net:-18307,  fee:7,  tax:0,   note:"" },
  // 2026-04-23
  { date:"2026-04-23", stock:"嘉澤",   action:"SELL", price:2570,  shares:10,   net:25613,   fee:10, tax:77,  note:"" },
  { date:"2026-04-23", stock:"新盛力", action:"SELL", price:157.5, shares:1000, net:157202,  fee:62, tax:236, note:"" },
  { date:"2026-04-23", stock:"新盛力", action:"BUY",  price:162.5, shares:1000, net:-162564, fee:64, tax:0,   note:"" },
  { date:"2026-04-23", stock:"新盛力", action:"BUY",  price:159,   shares:500,  net:-79531,  fee:31, tax:0,   note:"" },
  { date:"2026-04-23", stock:"新盛力", action:"BUY",  price:157.5, shares:100,  net:-15756,  fee:6,  tax:0,   note:"" },
  { date:"2026-04-23", stock:"譜瑞-KY",action:"SELL", price:632,   shares:100,  net:62986,   fee:25, tax:189, note:"" },
  // 2026-04-22
  { date:"2026-04-22", stock:"新盛力", action:"BUY",  price:152,   shares:1000, net:-152060, fee:60, tax:0,   note:"" },
  // 2026-04-21
  { date:"2026-04-21", stock:"譜瑞-KY",action:"SELL", price:530,   shares:150,  net:79231,   fee:31, tax:238, note:"" },
  { date:"2026-04-21", stock:"群聯",   action:"BUY",  price:1785,  shares:60,   net:-107142, fee:42, tax:0,   note:"" },
  // 2026-04-17
  { date:"2026-04-17", stock:"嘉澤",   action:"SELL", price:2510,  shares:15,   net:37523,   fee:15, tax:112, note:"" },
  // 2026-04-16
  { date:"2026-04-16", stock:"毅嘉",   action:"SELL", price:67.5,  shares:1000, net:67272,   fee:26, tax:202, note:"+19.4%" },
  // 2026-04-15
  { date:"2026-04-15", stock:"譜瑞-KY",action:"BUY",  price:532,   shares:50,   net:-26610,  fee:10, tax:0,   note:"" },
  // 2026-04-14
  { date:"2026-04-14", stock:"聯發科", action:"BUY",  price:1730,  shares:40,   net:-69227,  fee:27, tax:0,   note:"帶量突破，正常情緒" },
  { date:"2026-04-14", stock:"嘉澤",   action:"BUY",  price:2235,  shares:5,    net:-11179,  fee:4,  tax:0,   note:"" },
  { date:"2026-04-14", stock:"博智",   action:"SELL", price:313,   shares:100,  net:31195,   fee:12, tax:93,  note:"" },
  // 2026-04-13
  { date:"2026-04-13", stock:"研華",   action:"SELL", price:345,   shares:200,  net:68766,   fee:27, tax:207, note:"" },
  { date:"2026-04-13", stock:"研華",   action:"SELL", price:343.5, shares:150,  net:51351,   fee:20, tax:154, note:"" },
  { date:"2026-04-13", stock:"譜瑞-KY",action:"BUY",  price:538,   shares:30,   net:-16146,  fee:6,  tax:0,   note:"" },
  { date:"2026-04-13", stock:"譜瑞-KY",action:"BUY",  price:537,   shares:30,   net:-16116,  fee:6,  tax:0,   note:"" },
  { date:"2026-04-13", stock:"譜瑞-KY",action:"BUY",  price:536,   shares:30,   net:-16086,  fee:6,  tax:0,   note:"" },
  { date:"2026-04-13", stock:"譜瑞-KY",action:"BUY",  price:538,   shares:10,   net:-5382,   fee:2,  tax:0,   note:"" },
  { date:"2026-04-13", stock:"博智",   action:"SELL", price:315,   shares:100,  net:31394,   fee:12, tax:94,  note:"" },
  { date:"2026-04-13", stock:"博智",   action:"SELL", price:316,   shares:100,  net:31494,   fee:12, tax:94,  note:"" },
  // 2026-04-10
  { date:"2026-04-10", stock:"嘉澤",   action:"SELL", price:2285,  shares:5,    net:11387,   fee:4,  tax:34,  note:"" },
  { date:"2026-04-10", stock:"譜瑞-KY",action:"BUY",  price:527,   shares:100,  net:-52721,  fee:21, tax:0,   note:"" },
  { date:"2026-04-10", stock:"博智",   action:"SELL", price:320.5, shares:300,  net:95824,   fee:38, tax:288, note:"" },
  // 2026-04-09
  { date:"2026-04-09", stock:"毅嘉",   action:"BUY",  price:56.3,  shares:1000, net:-56322,  fee:22, tax:0,   note:"" },
  { date:"2026-04-09", stock:"奇鋐",   action:"SELL", price:2250,  shares:40,   net:89695,   fee:35, tax:270, note:"" },
  // 2026-04-08
  { date:"2026-04-08", stock:"奇鋐",   action:"BUY",  price:2170,  shares:40,   net:-86834,  fee:34, tax:0,   note:"" },
  { date:"2026-04-08", stock:"奇鋐",   action:"SELL", price:2170,  shares:40,   net:86506,   fee:34, tax:260, note:"當日沖銷" },
  { date:"2026-04-08", stock:"創意",   action:"BUY",  price:2500,  shares:20,   net:-50019,  fee:19, tax:0,   note:"" },
  // 2026-04-07
  { date:"2026-04-07", stock:"奇鋐",   action:"BUY",  price:2070,  shares:20,   net:-41416,  fee:16, tax:0,   note:"" },
  { date:"2026-04-07", stock:"奇鋐",   action:"SELL", price:2070,  shares:20,   net:41260,   fee:16, tax:124, note:"當日沖銷" },
  { date:"2026-04-07", stock:"創意",   action:"SELL", price:2340,  shares:10,   net:23321,   fee:9,  tax:70,  note:"" },
  { date:"2026-04-07", stock:"嘉澤",   action:"BUY",  price:2050,  shares:25,   net:-51270,  fee:20, tax:0,   note:"" },
  { date:"2026-04-07", stock:"貿聯-KY",action:"SELL", price:2025,  shares:20,   net:40363,   fee:16, tax:121, note:"" },
  // 2026-03 (選重要的)
  { date:"2026-03-31", stock:"元大台50",action:"BUY", price:73.35, shares:100,  net:-7337,   fee:2,  tax:0,   note:"" },
  { date:"2026-03-31", stock:"元大台50",action:"BUY", price:73.3,  shares:100,  net:-7332,   fee:2,  tax:0,   note:"" },
  { date:"2026-03-31", stock:"元大台50",action:"BUY", price:73.25, shares:100,  net:-7327,   fee:2,  tax:0,   note:"" },
  { date:"2026-03-31", stock:"元大台50",action:"BUY", price:73.2,  shares:100,  net:-7322,   fee:2,  tax:0,   note:"" },
  { date:"2026-03-31", stock:"元大台50",action:"BUY", price:73.15, shares:100,  net:-7317,   fee:2,  tax:0,   note:"" },
  { date:"2026-03-30", stock:"元大台50",action:"BUY", price:73.85, shares:500,  net:-36939,  fee:14, tax:0,   note:"" },
  { date:"2026-03-23", stock:"元大台50",action:"BUY", price:73.7,  shares:1000, net:-73729,  fee:29, tax:0,   note:"" },
  { date:"2026-03-23", stock:"國泰永續高股息",action:"BUY",price:21.96,shares:1000,net:-21968,fee:8,tax:0,   note:"" },
  { date:"2026-03-23", stock:"群益台灣精選高息",action:"BUY",price:22.4,shares:2000,net:-44817,fee:17,tax:0, note:"" },
  { date:"2026-03-19", stock:"奇鋐",   action:"SELL", price:2005,  shares:10,   net:19983,   fee:7,  tax:60,  note:"" },
  { date:"2026-03-16", stock:"奇鋐",   action:"SELL", price:1890,  shares:20,   net:37672,   fee:15, tax:113, note:"" },
  { date:"2026-03-16", stock:"力積電", action:"BUY",  price:67.1,  shares:1000, net:-67126,  fee:26, tax:0,   note:"" },
  { date:"2026-03-16", stock:"力積電", action:"SELL", price:66.1,  shares:1000, net:65975,   fee:26, tax:99,  note:"" },
  { date:"2026-03-16", stock:"頎邦",   action:"BUY",  price:60,    shares:1000, net:-60023,  fee:23, tax:0,   note:"" },
  { date:"2026-03-17", stock:"頎邦",   action:"SELL", price:63.4,  shares:1000, net:63185,   fee:25, tax:190, note:"+5.3%" },
  { date:"2026-03-12", stock:"奇鋐",   action:"SELL", price:1900,  shares:10,   net:18936,   fee:7,  tax:57,  note:"" },
  { date:"2026-03-06", stock:"奇鋐",   action:"SELL", price:1850,  shares:10,   net:18438,   fee:7,  tax:55,  note:"" },
  { date:"2026-03-05", stock:"奇鋐",   action:"SELL", price:1805,  shares:10,   net:17989,   fee:7,  tax:54,  note:"" },
  // 2026-01 ~ 02 (選重要的)
  { date:"2026-01-30", stock:"奇鋐",   action:"SELL", price:1455,  shares:40,   net:58003,   fee:23, tax:174, note:"分批出場" },
  { date:"2026-01-30", stock:"貿聯-KY",action:"BUY",  price:1300,  shares:40,   net:-52020,  fee:20, tax:0,   note:"" },
  { date:"2026-01-21", stock:"貿聯-KY",action:"BUY",  price:1300,  shares:20,   net:-26010,  fee:10, tax:0,   note:"" },
  { date:"2026-01-19", stock:"中興電", action:"BUY",  price:157,   shares:500,  net:-78531,  fee:31, tax:0,   note:"" },
  { date:"2026-01-19", stock:"中興電", action:"SELL", price:160.5, shares:500,  net:79978,   fee:32, tax:240, note:"+1.8%" },
  { date:"2026-01-27", stock:"智邦",   action:"BUY",  price:1175,  shares:50,   net:-58773,  fee:23, tax:0,   note:"" },
  { date:"2026-01-30", stock:"智邦",   action:"SELL", price:1150,  shares:50,   net:57306,   fee:22, tax:172, note:"-2.5%" },
  { date:"2026-01-29", stock:"世芯-KY",action:"SELL", price:3280,  shares:15,   net:49034,   fee:19, tax:147, note:"前期持有出清" },
  { date:"2026-01-27", stock:"世芯-KY",action:"SELL", price:3445,  shares:15,   net:51500,   fee:20, tax:155, note:"" },
  { date:"2026-01-08", stock:"世芯-KY",action:"SELL", price:3615,  shares:20,   net:72056,   fee:28, tax:216, note:"" },
  { date:"2026-01-08", stock:"奇鋐",   action:"BUY",  price:1385,  shares:100,  net:-138555, fee:55, tax:0,   note:"主力進場" },
  { date:"2026-01-13", stock:"奇鋐",   action:"BUY",  price:1355,  shares:10,   net:-13555,  fee:5,  tax:0,   note:"" },
  { date:"2026-01-19", stock:"奇鋐",   action:"BUY",  price:1295,  shares:20,   net:-25910,  fee:10, tax:0,   note:"" },
  { date:"2026-01-21", stock:"奇鋐",   action:"BUY",  price:1285,  shares:10,   net:-12855,  fee:5,  tax:0,   note:"" },
  { date:"2026-01-02", stock:"達麗",   action:"SELL", price:52.9,  shares:1000, net:52721,   fee:21, tax:158, note:"前期持有出清" },
  { date:"2026-01-02", stock:"達麗",   action:"SELL", price:52.8,  shares:1000, net:52621,   fee:21, tax:158, note:"" },
  { date:"2026-01-02", stock:"達麗",   action:"SELL", price:52.2,  shares:1000, net:52024,   fee:20, tax:156, note:"" },
  { date:"2026-02-23", stock:"貿聯-KY",action:"SELL", price:1330,  shares:50,   net:66275,   fee:26, tax:199, note:"" },
  { date:"2026-02-23", stock:"貿聯-KY",action:"SELL", price:1315,  shares:50,   net:65527,   fee:26, tax:197, note:"" },
  { date:"2026-02-11", stock:"貿聯-KY",action:"SELL", price:1370,  shares:40,   net:54615,   fee:21, tax:164, note:"" },
  { date:"2026-03-18", stock:"貿聯-KY",action:"SELL", price:1700,  shares:20,   net:33885,   fee:13, tax:102, note:"" },
  { date:"2026-06-03", stock:"明泰",   action:"SELL", price:39.1,  shares:3000, net:117207,  fee:47, tax:351, note:"+1.34%" },
  { date:"2026-06-04", stock:"雙鴻",   action:"BUY",  price:1200,  shares:30,   net:-36018,  fee:18, tax:0,   note:"回五日線反彈量縮" },
];
