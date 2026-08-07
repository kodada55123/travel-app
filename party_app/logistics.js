// 住宿與交通配置快照；來源：Google 試算表「人事資料表」的「房間」「車輛」分頁
// 讀取日期：2026-08-07（Asia/Taipei）
window.PARTY_LOGISTICS = {
  updated: "2026-08-07",
  rooms: [
    { room: "101", type: "4人房", beds: ["小柯", "彥霖", "小祥", "葉小刺", "柏儒-睡墊"] },
    { room: "102", type: "4人房", beds: ["岳彤", "漢克", "西瓜", "鉦倫"] },
    { room: "103", type: "4人房", beds: ["Eric Chuang", "RGAO", "Benny", "Kevin凱"] },
    { room: "105", type: "4人房", beds: ["石頭", "昆yeh", "Chung", "Asics Cu"] },
    { room: "201", type: "2人房", beds: ["Tyler", "Statham"] },
    { room: "202", type: "4人房", beds: ["En", "Jonathan", "賢", "Tony"] },
    { room: "301", type: "4人房", beds: ["Alex", "Wadeee", "小温", "堯"] },
    { room: "302", type: "6人房", beds: ["Daniel Yeh", "羅", "William🥵", "Deacon", "leo", "哲"] },
    { room: "303", type: "4人房", beds: ["柏一", "ERIC歐", "毛毛", "Hank lin"] },
    { room: "305", type: "6人房", beds: ["女神", "Roy Kao", "宇昌", "黃世輝", "大大", "吳炫"] },
    { room: "501", type: "6人房", beds: ["威丞", "Weiyo", "小王子", "Ren", "偉傑🐧", "east"] },
    { room: "502", type: "5人房", beds: ["Timmy", "Horus", "黃寯寬", "水豚BO", "藍²"] },
  ],
  cars: [
    { driver: "小柯", from: "桃園八德", passengers: ["彥霖", "石頭-中壢", "昆yeh-中壢"] },
    { driver: "Statham", from: "捷運新店區公所", passengers: ["Tyler", "葉小刺", "賢"] },
    { driver: "Alex", from: "台北南港", passengers: ["Daniel Yeh", "羅", "Timmy"] },
    { driver: "哲", from: "新竹", passengers: ["Ren", "Chung-台中", "Asics Cu-台中", "Horus-竹南"] },
    { driver: "毛毛", from: "台北龍山寺捷運站", passengers: ["Hank lin", "Eric Chuang", "RGAO"] },
    { driver: "Kevin凱", from: "港墘站", passengers: ["Benny", "世哲", "藍²", "柏儒"] },
    { driver: "堯", from: "板橋捷運站", passengers: ["偉傑🐧", "小温", "east"] },
    { driver: "小王子", from: "桃園高鐵", passengers: ["小祥", "William🥵-林口", "Deacon"] },
    { driver: "黃寯寬", from: "明德", passengers: ["Tony", "黃世輝wayne", "宇昌"] },
    { driver: "威丞", from: "台北", passengers: ["ERIC歐", "柏一", "Weiyo"] },
    { driver: "Roy Kao", from: "台北車站/南港車站", passengers: ["女神", "漢克", "岳彤"] },
    { driver: "吳炫", from: "新北土城", passengers: ["大大", "leo", "水豚BO"] },
    { driver: "Jonathan", from: "台南", passengers: ["En", "Wadeee-台中高鐵", "鉦倫-嘉義交流道"] },
  ],
};
