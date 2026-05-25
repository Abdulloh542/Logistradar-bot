"""
Demo ma'lumotlar bazaga yozish (bot birinchi marta ishlaganda)
"""
import asyncio
from utils.db import add_ad, get_ad_count

DEMO_ADS = [
    {"from_loc":"Toshkent","to_loc":"Baku","weight":"22.5t","truck":"Tent","cargo":"соки","price":"perechisleniya","km":3059,"hours":42.8,"phone":"+998901234567","link":"","customs":"","source":"LogiNet"},
    {"from_loc":"Toshkent","to_loc":"Andijon","weight":"15t","truck":"Tent","cargo":"трансформатор","price":"","km":345,"hours":6.1,"phone":"+998712345678","link":"","customs":"","source":"Logistradar"},
    {"from_loc":"Toshkent","to_loc":"Bishkek","weight":"22t","truck":"Tent","cargo":"труба профил","price":"","km":633,"hours":9.3,"phone":"+998991234567","link":"","customs":"","source":"CargoUz"},
    {"from_loc":"Toshkent","to_loc":"Moskva","weight":"15.5t","truck":"Tent","cargo":"спанлейс рулон","price":"","km":3528,"hours":47.5,"phone":"+998881234567","link":"","customs":"Самара","source":"LogiNet"},
    {"from_loc":"Samarqand","to_loc":"Moskva","weight":"20t","truck":"Ref","cargo":"meva","price":"800 USD","km":3200,"hours":45,"phone":"+998901230001","link":"","customs":"","source":"LogiNet"},
    {"from_loc":"Buxoro","to_loc":"Qozog'iston","weight":"18t","truck":"Tent","cargo":"paxta","price":"600 USD","km":890,"hours":14,"phone":"+998901230002","link":"","customs":"","source":"CargoUz"},
    {"from_loc":"Namangan","to_loc":"Toshkent","weight":"10t","truck":"Katta Isuzu","cargo":"sabzavot","price":"200 USD","km":320,"hours":5.5,"phone":"+998901230003","link":"","customs":"","source":"FreightUz"},
    {"from_loc":"Andijon","to_loc":"Rossiya","weight":"24t","truck":"Ref","cargo":"qovun","price":"1200 USD","km":3600,"hours":50,"phone":"+998901230004","link":"","customs":"","source":"Logistradar"},
    {"from_loc":"Toshkent","to_loc":"Stambul","weight":"20t","truck":"Tent","cargo":"tekstil","price":"2000 USD","km":4500,"hours":65,"phone":"+998901230005","link":"","customs":"","source":"LogiNet"},
    {"from_loc":"Qarshi","to_loc":"Toshkent","weight":"8t","truck":"Isuzu","cargo":"gaz ballonlari","price":"300 USD","km":450,"hours":7,"phone":"+998901230006","link":"","customs":"","source":"CargoUz"},
    {"from_loc":"Toshkent","to_loc":"Germaniya","weight":"22t","truck":"Tent","cargo":"avtozapchast","price":"3500 USD","km":6200,"hours":90,"phone":"+998901230007","link":"","customs":"","source":"FreightUz"},
    {"from_loc":"Urganch","to_loc":"Toshkent","weight":"15t","truck":"Ref rejimsiz","cargo":"baliq","price":"400 USD","km":1100,"hours":18,"phone":"+998901230008","link":"","customs":"","source":"Logistradar"},
    {"from_loc":"Toshkent","to_loc":"Belarus","weight":"20t","truck":"Tent","cargo":"don","price":"1800 USD","km":4100,"hours":58,"phone":"+998901230009","link":"","customs":"","source":"LogiNet"},
    {"from_loc":"Farg'ona","to_loc":"Qirg'iziston","weight":"12t","truck":"Tent","cargo":"poliz","price":"500 USD","km":280,"hours":5,"phone":"+998901230010","link":"","customs":"","source":"CargoUz"},
    {"from_loc":"Toshkent","to_loc":"Gruziya","weight":"18t","truck":"Ref","cargo":"go'sht","price":"1500 USD","km":2800,"hours":40,"phone":"+998901230011","link":"","customs":"","source":"FreightUz"},
    {"from_loc":"Termiz","to_loc":"Tojikiston","weight":"10t","truck":"Bortovoy","cargo":"sement","price":"300 USD","km":180,"hours":3,"phone":"+998901230012","link":"","customs":"","source":"Logistradar"},
    {"from_loc":"Nukus","to_loc":"Toshkent","weight":"20t","truck":"Tent","cargo":"paxta tolasi","price":"700 USD","km":1400,"hours":22,"phone":"+998901230013","link":"","customs":"","source":"LogiNet"},
    {"from_loc":"Toshkent","to_loc":"Ozarbayjon","weight":"22t","truck":"Ref","cargo":"sharbat","price":"900 USD","km":2200,"hours":32,"phone":"+998901230014","link":"","customs":"","source":"CargoUz"},
    {"from_loc":"Gazalkent","to_loc":"Denov","weight":"","truck":"","cargo":"","price":"","km":799,"hours":13.2,"phone":"+998901112233","link":"","customs":"","source":"FreightUz"},
    {"from_loc":"Toshkent","to_loc":"Rossiya","weight":"21t","truck":"Tent","cargo":"qurilish materiallari","price":"1100 USD","km":3400,"hours":48,"phone":"+998901230015","link":"","customs":"","source":"Logistradar"},
]

async def seed_if_empty():
    count = await get_ad_count()
    if count == 0:
        for ad in DEMO_ADS:
            await add_ad(ad)
        print(f"[OK] {len(DEMO_ADS)} ta demo e'lon bazaga yozildi")
    else:
        print(f"[INFO] Bazada allaqachon {count} ta e'lon bor")

if __name__ == "__main__":
    import asyncio
    from utils.db import init_db
    async def run():
        await init_db()
        await seed_if_empty()
    asyncio.run(run())
