"""
Product master data: 1,000+ electronics SKUs sold in India.

Each SKU is one model in one configuration (RAM / storage / size / capacity).
Colours are not separate SKUs because stores price colours identically.

Prices are APPROXIMATE Indian market prices (INR) for illustration: `mrp` is
the list/launch price, `base_price` the typical current selling price.
`launch` is set for models released inside the dataset window, so their price
history starts on launch day.  For brand-new models released after this
catalogue was compiled, use the live SerpAPI source.
"""
from __future__ import annotations

PRODUCTS: list[dict] = []


def _r(x: float) -> int:
    """Round to Indian retail endings."""
    if x >= 5000:
        return int(round(x / 100.0) * 100 - 1)
    return int(round(x / 10.0) * 10 - 1)


def _add(brand, model, spec, category, mrp, price, color="Black", launch=None, sub=None):
    PRODUCTS.append({"brand": brand, "model": model, "spec": spec, "category": category,
                     "mrp": int(mrp), "base_price": int(min(price, mrp)), "color": color,
                     "launch": launch, "sub": sub})


def _st(gb) -> str:
    return f"{gb // 1024} TB" if isinstance(gb, int) and gb >= 1024 else f"{gb} GB"


# ---------------------------------------------------------------------------
# Smartphones
# ---------------------------------------------------------------------------
def apple_phone(model, rows, launch=None, color="Black"):
    for storage, mrp, price in rows:
        _add("Apple", model, _st(storage), "Smartphone", mrp, price, color, launch)


def phone(brand, model, rows, launch=None, color="Black", markup=1.15):
    for ram, storage, price in rows:
        _add(brand, model, f"{ram} GB RAM, {_st(storage)}", "Smartphone",
             _r(price * markup), price, color, launch)


apple_phone("iPhone 17", [(256, 82900, 82900), (512, 102900, 102900)], "2025-09-19", "Lavender")
apple_phone("iPhone Air", [(256, 119900, 119900), (512, 139900, 139900), (1024, 159900, 159900)], "2025-09-19", "Sky Blue")
apple_phone("iPhone 17 Pro", [(256, 134900, 134900), (512, 154900, 154900), (1024, 174900, 174900)], "2025-09-19", "Cosmic Orange")
apple_phone("iPhone 17 Pro Max", [(256, 149900, 149900), (512, 169900, 169900), (1024, 189900, 189900),
                                  (2048, 229900, 229900)], "2025-09-19", "Deep Blue")
apple_phone("iPhone 16", [(128, 69900, 64900), (256, 79900, 74900), (512, 99900, 94900)])
apple_phone("iPhone 16 Plus", [(128, 79900, 72900), (256, 89900, 82900), (512, 109900, 102900)], color="Teal")
apple_phone("iPhone 16 Pro", [(128, 119900, 109900), (256, 129900, 119900), (512, 149900, 139900)], color="Desert Titanium")
apple_phone("iPhone 16 Pro Max", [(256, 144900, 134900), (512, 164900, 154900), (1024, 184900, 174900)], color="Natural Titanium")
apple_phone("iPhone 16e", [(128, 59900, 54900), (256, 69900, 64900), (512, 89900, 84900)], "2025-02-28", "White")
apple_phone("iPhone 15", [(128, 59900, 54900), (256, 69900, 64900), (512, 89900, 84900)], color="Blue")
apple_phone("iPhone 15 Plus", [(128, 69900, 63900), (256, 79900, 73900)], color="Pink")
apple_phone("iPhone 14", [(128, 59900, 52900), (256, 69900, 62900)], color="Midnight")

S = "Samsung"
phone(S, "Galaxy S25 Ultra", [(12, 256, 119999), (12, 512, 131999), (12, 1024, 155999)], "2025-02-07", "Titanium Silverblue", 1.08)
phone(S, "Galaxy S25+", [(12, 256, 89999), (12, 512, 101999)], "2025-02-07", "Navy", 1.1)
phone(S, "Galaxy S25", [(12, 128, 74999), (12, 256, 79999), (12, 512, 91999)], "2025-02-07", "Icyblue", 1.08)
phone(S, "Galaxy S25 Edge", [(12, 256, 99999), (12, 512, 111999)], "2025-05-30", "Titanium Jetblack", 1.1)
phone(S, "Galaxy S25 FE", [(8, 128, 54999), (8, 256, 59999), (8, 512, 71999)], "2025-09-04", "Jetblack", 1.1)
phone(S, "Galaxy S24 Ultra", [(12, 256, 99999), (12, 512, 109999)], color="Titanium Gray", markup=1.3)
phone(S, "Galaxy S24 FE", [(8, 128, 35999), (8, 256, 41999)], color="Graphite", markup=1.6)
phone(S, "Galaxy S24", [(8, 128, 49999), (8, 256, 54999)], color="Onyx Black", markup=1.5)
phone(S, "Galaxy Z Fold7", [(12, 256, 174999), (12, 512, 186999), (16, 1024, 210999)], "2025-07-25", "Blue Shadow", 1.05)
phone(S, "Galaxy Z Flip7", [(12, 256, 109999), (12, 512, 121999)], "2025-07-25", "Coralred", 1.05)
phone(S, "Galaxy Z Flip7 FE", [(8, 128, 89999), (8, 256, 95999)], "2025-07-25", "Black", 1.05)
phone(S, "Galaxy A56 5G", [(8, 128, 41999), (8, 256, 44999), (12, 256, 47999)], "2025-03-03", "Awesome Graphite")
phone(S, "Galaxy A36 5G", [(8, 128, 30999), (8, 256, 33999), (12, 256, 36999)], "2025-03-03", "Awesome Lavender")
phone(S, "Galaxy A26 5G", [(8, 128, 24999), (8, 256, 27999)], "2025-03-28", "Awesome Black")
phone(S, "Galaxy A16 5G", [(6, 128, 16999), (8, 128, 18999), (8, 256, 21999)], color="Light Green")
phone(S, "Galaxy A06 5G", [(4, 128, 11499), (6, 128, 12999)], "2025-07-01", "Gray")
phone(S, "Galaxy M56 5G", [(8, 128, 26999), (8, 256, 29999)], "2025-04-23", "Light Green")
phone(S, "Galaxy M36 5G", [(6, 128, 16499), (8, 128, 17999), (8, 256, 20999)], "2025-07-05", "Orange Haze")
phone(S, "Galaxy M16 5G", [(4, 128, 11499), (6, 128, 12999), (8, 128, 14499)], "2025-03-05", "Thunder Black")
phone(S, "Galaxy M06 5G", [(4, 128, 9499), (6, 128, 10999)], "2025-03-05", "Sage Green")
phone(S, "Galaxy F56 5G", [(8, 128, 25999), (8, 256, 28999)], "2025-05-14", "Green")
phone(S, "Galaxy F36 5G", [(6, 128, 17499), (8, 128, 18999)], "2025-07-29", "Coral Red")
phone(S, "Galaxy F16 5G", [(4, 128, 11499), (6, 128, 12999), (8, 128, 14499)], "2025-03-13", "Vibing Blue")
phone(S, "Galaxy F06 5G", [(4, 128, 9499), (6, 128, 10999)], "2025-02-12", "Bahama Blue")

O = "OnePlus"
phone(O, "13", [(12, 256, 69999), (16, 512, 76999), (24, 1024, 89999)], "2025-01-10", "Black Eclipse", 1.05)
phone(O, "13R", [(12, 256, 42999), (16, 512, 49999)], "2025-01-10", "Nebula Noir", 1.05)
phone(O, "13s", [(12, 256, 54999), (12, 512, 59999)], "2025-06-12", "Black Velvet", 1.05)
phone(O, "Nord 5", [(8, 256, 31999), (12, 256, 34999), (12, 512, 37999)], "2025-07-12", "Phantom Grey", 1.06)
phone(O, "Nord CE5", [(8, 128, 24999), (8, 256, 26999), (12, 256, 28999)], "2025-07-12", "Black Infinity", 1.06)
phone(O, "Nord 4", [(8, 128, 29999), (8, 256, 32999), (12, 256, 35999)], color="Obsidian Midnight", markup=1.1)
phone(O, "Nord CE4 Lite 5G", [(8, 128, 17999), (8, 256, 19999)], color="Super Silver", markup=1.12)
phone(O, "12R", [(8, 128, 37999), (16, 256, 42999)], color="Iron Gray", markup=1.15)

G = "Google"
phone(G, "Pixel 10", [(12, 256, 79999)], "2025-08-28", "Obsidian", 1.0)
phone(G, "Pixel 10 Pro", [(16, 256, 109999), (16, 512, 124999)], "2025-08-28", "Obsidian", 1.0)
phone(G, "Pixel 10 Pro XL", [(16, 256, 124999), (16, 512, 139999)], "2025-08-28", "Moonstone", 1.0)
phone(G, "Pixel 10 Pro Fold", [(16, 256, 172999)], "2025-10-09", "Moonstone", 1.0)
phone(G, "Pixel 9a", [(8, 256, 49999)], "2025-04-16", "Obsidian", 1.0)
phone(G, "Pixel 9", [(12, 256, 64999)], color="Porcelain", markup=1.23)
phone(G, "Pixel 9 Pro XL", [(16, 256, 99999)], color="Hazel", markup=1.25)

X = "Xiaomi"
phone("Redmi", "Note 14 5G", [(6, 128, 17999), (8, 128, 18999), (8, 256, 20999)], "2024-12-13", "Titan Black")
phone("Redmi", "Note 14 Pro 5G", [(8, 128, 23999), (8, 256, 25999), (12, 512, 28999)], "2024-12-13", "Phantom Purple")
phone("Redmi", "Note 14 Pro+ 5G", [(8, 256, 30999), (12, 256, 32999), (12, 512, 35999)], "2024-12-13", "Spectre Blue")
phone("Redmi", "15 5G", [(6, 128, 14999), (8, 128, 15999), (8, 256, 16999)], "2025-08-28", "Midnight Black")
phone("Redmi", "14C 5G", [(4, 64, 9999), (4, 128, 10999), (6, 128, 11999)], "2025-01-10", "Starlight Blue")
phone("Redmi", "A5", [(3, 64, 6499), (4, 128, 7499)], "2025-04-16", "Jaisalmer Gold")
phone("Redmi", "13 5G", [(6, 128, 13499), (8, 128, 14999)], color="Hawaiian Blue", markup=1.3)
phone(X, "15", [(12, 512, 64999)], "2025-03-11", "Black", 1.05)
phone(X, "15 Ultra", [(16, 512, 109999)], "2025-03-11", "Silver Chrome", 1.05)
phone(X, "14 CIVI", [(8, 256, 39999), (12, 512, 45999)], color="Shadow Black", markup=1.2)
phone("Poco", "F7 5G", [(12, 256, 31999), (12, 512, 33999)], "2025-07-01", "Phantom Black", 1.1)
phone("Poco", "X7 5G", [(8, 128, 21999), (8, 256, 23999)], "2025-01-14", "Glacier Green")
phone("Poco", "X7 Pro 5G", [(8, 256, 27999), (12, 256, 29999)], "2025-01-14", "Nebula Green")
phone("Poco", "M7 Pro 5G", [(6, 128, 14999), (8, 256, 16999)], "2024-12-20", "Lavender Frost")
phone("Poco", "M7 5G", [(6, 128, 10499), (8, 128, 11499)], "2025-03-07", "Mint Green")
phone("Poco", "C75 5G", [(4, 64, 7999)], "2024-12-19", "Enchanted Green")

R = "realme"
phone(R, "GT 7", [(12, 256, 39999), (12, 512, 42999)], "2025-05-30", "IceSense Black", 1.12)
phone(R, "GT 7T", [(8, 256, 34999), (12, 256, 37999), (12, 512, 41999)], "2025-05-30", "Racing Yellow", 1.12)
phone(R, "15 Pro 5G", [(8, 128, 31999), (8, 256, 33999), (12, 256, 35999), (12, 512, 38999)], "2025-07-30", "Velvet Green")
phone(R, "15 5G", [(8, 128, 25999), (8, 256, 27999), (12, 256, 30999)], "2025-07-30", "Flowing Silver")
phone(R, "P3 Pro 5G", [(8, 128, 23999), (8, 256, 24999), (12, 256, 26999)], "2025-02-18", "Nebula Glow")
phone(R, "P3 5G", [(6, 128, 16999), (8, 128, 17999), (8, 256, 19999)], "2025-03-19", "Comet Grey")
phone(R, "P3x 5G", [(6, 128, 13999), (8, 128, 14999)], "2025-02-18", "Midnight Blue")
phone(R, "Narzo 80 Pro 5G", [(8, 128, 19999), (8, 256, 21499), (12, 256, 23499)], "2025-04-09", "Speed Silver")
phone(R, "Narzo 80x 5G", [(6, 128, 13999), (8, 128, 14999)], "2025-04-09", "Deep Ocean")
phone(R, "C75 5G", [(4, 128, 12999), (6, 128, 13999)], "2025-05-20", "Lily White")

V = "vivo"
phone(V, "X200 Pro", [(16, 512, 94999)], "2024-12-19", "Titanium Grey", 1.05)
phone(V, "X200", [(12, 256, 65999), (16, 512, 71999)], "2024-12-19", "Cosmos Black", 1.05)
phone(V, "X200 FE", [(12, 256, 54999), (16, 512, 59999)], "2025-07-23", "Amber Yellow", 1.05)
phone(V, "X Fold5", [(16, 512, 149999)], "2025-07-14", "Titanium Gray", 1.0)
phone(V, "V60", [(8, 128, 36999), (8, 256, 38999), (12, 256, 40999), (16, 512, 45999)], "2025-08-19", "Mist Gray", 1.08)
phone(V, "V50", [(8, 128, 34999), (8, 256, 36999), (12, 512, 40999)], "2025-02-25", "Rose Red", 1.08)
phone(V, "V50e", [(8, 128, 28999), (8, 256, 30999)], "2025-04-17", "Sapphire Blue", 1.08)
phone(V, "T4 5G", [(8, 128, 21999), (8, 256, 23999), (12, 256, 25999)], "2025-04-29", "Emerald Blaze")
phone(V, "T4x 5G", [(6, 128, 13999), (8, 128, 14999), (8, 256, 16999)], "2025-03-12", "Marine Blue")
phone(V, "T4 Ultra", [(8, 256, 37999), (12, 256, 39999), (12, 512, 41999)], "2025-06-18", "Phoenix Gold")
phone(V, "Y39 5G", [(8, 128, 16999), (8, 256, 18999)], "2025-03-25", "Ocean Blue")
phone(V, "Y29 5G", [(4, 128, 13999), (6, 128, 15499), (8, 128, 16999)], "2025-01-23", "Diamond Black")

phone("iQOO", "13 5G", [(12, 256, 54999), (16, 512, 59999)], "2024-12-11", "Legend", 1.1)
phone("iQOO", "Neo 10 5G", [(8, 128, 31999), (8, 256, 33999), (12, 256, 35999), (16, 512, 40999)], "2025-06-03", "Titanium Chrome", 1.1)
phone("iQOO", "Neo 10R 5G", [(8, 128, 26999), (8, 256, 28999), (12, 256, 30999)], "2025-03-18", "Raging Blue", 1.1)
phone("iQOO", "Z10 5G", [(8, 128, 21999), (8, 256, 23999), (12, 256, 25999)], "2025-04-16", "Stellar Black", 1.1)
phone("iQOO", "Z10x 5G", [(6, 128, 13499), (8, 128, 14999), (8, 256, 16499)], "2025-04-16", "Titanium", 1.1)
phone("iQOO", "Z10R 5G", [(8, 128, 19499), (8, 256, 21499), (12, 256, 23499)], "2025-07-24", "Aquamarine", 1.1)

OP = "OPPO"
phone(OP, "Find X8 Pro", [(16, 512, 99999)], "2024-11-28", "Pearl White", 1.05)
phone(OP, "Find X8", [(12, 256, 69999), (16, 512, 79999)], "2024-11-28", "Space Black", 1.05)
phone(OP, "Reno14 Pro 5G", [(12, 256, 49999), (12, 512, 54999)], "2025-07-08", "Titanium Grey", 1.08)
phone(OP, "Reno14 5G", [(8, 256, 37999), (12, 256, 39999), (12, 512, 42999)], "2025-07-08", "Forest Green", 1.08)
phone(OP, "F29 Pro 5G", [(8, 128, 27999), (8, 256, 29999), (12, 256, 31999)], "2025-03-27", "Marble White")
phone(OP, "F29 5G", [(8, 128, 23999), (8, 256, 25999)], "2025-03-27", "Glacier Blue")
phone(OP, "K13 5G", [(8, 128, 17999), (8, 256, 19999)], "2025-04-25", "Icy Purple")
phone(OP, "A5 Pro 5G", [(8, 128, 17999), (8, 256, 19999)], "2025-04-24", "Feather Blue")

M = "Motorola"
phone(M, "Edge 60 Pro", [(8, 256, 29999), (12, 256, 33999)], "2025-04-30", "Pantone Shadow", 1.1)
phone(M, "Edge 60 Fusion", [(8, 256, 22999), (12, 256, 24999)], "2025-04-09", "Pantone Amazonite", 1.1)
phone(M, "Edge 60", [(12, 256, 25999)], "2025-06-10", "Pantone Gibraltar Sea", 1.1)
phone(M, "Edge 60 Stylus", [(8, 256, 22999)], "2025-04-15", "Pantone Surf The Web", 1.1)
phone(M, "Edge 50 Pro", [(8, 256, 27999), (12, 256, 31999)], color="Moonlight Pearl", markup=1.3)
phone(M, "G96 5G", [(8, 128, 17999), (8, 256, 19999)], "2025-07-09", "Pantone Ashleigh Blue")
phone(M, "G85 5G", [(8, 128, 17999), (12, 256, 19999)], color="Cobalt Blue")
phone(M, "G45 5G", [(4, 128, 9999), (8, 128, 11999)], color="Brilliant Blue")
phone(M, "G35 5G", [(4, 128, 9999)], color="Guava Red")
phone(M, "Razr 60 Ultra", [(16, 512, 99999)], "2025-05-13", "Pantone Rio Red", 1.0)
phone(M, "Razr 60", [(8, 256, 49999)], "2025-05-28", "Pantone Gibraltar Sea", 1.0)

N = "Nothing"
phone(N, "Phone (3)", [(12, 256, 79999), (16, 512, 89999)], "2025-07-15", "White", 1.0)
phone(N, "Phone (3a) Pro", [(8, 128, 29999), (8, 256, 31999), (12, 256, 33999)], "2025-03-11", "Grey", 1.0)
phone(N, "Phone (3a)", [(8, 128, 24999), (8, 256, 26999)], "2025-03-11", "White", 1.0)
phone(N, "Phone (2a) Plus", [(8, 256, 27999), (12, 256, 29999)], color="Black", markup=1.0)
phone("CMF by Nothing", "Phone 2 Pro", [(8, 128, 18999), (8, 256, 20999)], "2025-05-05", "Orange", 1.0)
phone("Lava", "Agni 3 5G", [(8, 128, 20999), (8, 256, 22999)], color="Pristine Glass", markup=1.2)
phone("Lava", "Blaze Duo 5G", [(6, 128, 16999), (8, 128, 17999)], color="Celestial Blue", markup=1.2)
phone("Infinix", "GT 30 Pro 5G", [(8, 256, 24999), (12, 256, 26999)], "2025-06-03", "Blade White", 1.2)
phone("Infinix", "Note 50s 5G+", [(8, 128, 15999), (8, 256, 17999)], "2025-04-18", "Titanium Grey", 1.2)
phone("Infinix", "Hot 60 5G+", [(6, 128, 10499)], "2025-07-11", "Shadow Blue", 1.2)
phone("Tecno", "Pova 7 Pro 5G", [(8, 128, 18999), (8, 256, 19999)], "2025-07-04", "Dynamic Grey", 1.2)
phone("Tecno", "Camon 40 Pro 5G", [(8, 256, 22999)], "2025-05-23", "Emerald Lake Green", 1.2)
phone("Tecno", "Spark 40 Pro+", [(8, 256, 16999)], "2025-08-20", "Titanium Black", 1.2)


# ---------------------------------------------------------------------------
# Laptops
# ---------------------------------------------------------------------------
TIERS = {
    "budget": [(8, "512 GB", -4000), (16, "512 GB", 0)],
    "std": [(8, "512 GB", -5000), (16, "512 GB", 0), (16, "1 TB", 6000)],
    "gaming": [(16, "512 GB", 0), (16, "1 TB", 7000), (32, "1 TB", 17000)],
    "premium": [(16, "512 GB", 0), (16, "1 TB", 12000), (32, "1 TB", 30000)],
}


def laptop(brand, model, price, tier="std", launch=None, color="Grey", markup=1.3):
    for ram, ssd, delta in TIERS[tier]:
        p = price + delta
        _add(brand, model, f"{ram} GB RAM, {ssd} SSD", "Laptop", _r(p * markup), _r(p), color, launch)


def macbook(model, rows, launch=None, color="Midnight"):
    for ram, ssd, mrp, price in rows:
        _add("Apple", model, f"{ram} GB RAM, {ssd} SSD", "Laptop", mrp, price, color, launch)


macbook("MacBook Air 13-inch M4", [(16, "256 GB", 99900, 94900), (16, "512 GB", 119900, 114900),
                                   (24, "512 GB", 139900, 134900)], "2025-03-12", "Sky Blue")
macbook("MacBook Air 15-inch M4", [(16, "256 GB", 124900, 119900), (16, "512 GB", 144900, 139900),
                                   (24, "512 GB", 164900, 159900)], "2025-03-12", "Starlight")
macbook("MacBook Air 13-inch M3", [(16, "256 GB", 114900, 89900), (16, "512 GB", 134900, 109900)])
macbook("MacBook Pro 14-inch M4", [(16, "512 GB", 169900, 164900), (16, "1 TB", 189900, 184900),
                                   (24, "1 TB", 209900, 204900)], "2024-11-08", "Space Black")
macbook("MacBook Pro 14-inch M4 Pro", [(24, "512 GB", 199900, 194900), (24, "1 TB", 239900, 234900)], "2024-11-08", "Space Black")
macbook("MacBook Pro 16-inch M4 Pro", [(24, "512 GB", 249900, 244900), (48, "512 GB", 289900, 284900)], "2024-11-08", "Silver")

laptop("HP", "Victus 15 AMD Ryzen 5 7535HS RTX 2050 Gaming Laptop", 55990, "gaming", color="Mica Silver")
laptop("HP", "Victus 15 Intel Core i5 12450H RTX 3050 Gaming Laptop", 64990, "gaming", color="Mica Silver")
laptop("HP", "Victus 16 AMD Ryzen 7 8845HS RTX 4060 Gaming Laptop", 99990, "gaming", color="Performance Blue")
laptop("HP", "Omen 16 AMD Ryzen 7 8845HS RTX 4060 Gaming Laptop", 124990, "gaming", color="Shadow Black")
laptop("HP", "Pavilion 15 Intel Core i5 1335U Laptop", 62990, color="Natural Silver")
laptop("HP", "Pavilion x360 14 Intel Core i5 1335U 2-in-1 Laptop", 69990, color="Natural Silver")
laptop("HP", "15s AMD Ryzen 5 5500U Laptop", 42990, "budget", color="Natural Silver")
laptop("HP", "15 Intel Core i3 1315U Laptop", 36990, "budget", color="Natural Silver")
laptop("HP", "Envy x360 14 Intel Core Ultra 5 125U 2-in-1 Laptop", 89990, "premium", color="Meteor Silver")
laptop("HP", "OmniBook 5 Snapdragon X Plus Laptop", 74990, "premium", "2025-04-15", "Glacier Silver")
laptop("Dell", "Inspiron 3530 Intel Core i3 1305U Laptop", 37990, "budget", color="Platinum Silver")
laptop("Dell", "Inspiron 3530 Intel Core i5 1334U Laptop", 52990, color="Platinum Silver")
laptop("Dell", "Inspiron 3530 Intel Core i7 1355U Laptop", 66990, color="Platinum Silver")
laptop("Dell", "Inspiron 5440 Intel Core 5 120U Laptop", 64990, color="Ice Blue")
laptop("Dell", "Vostro 3520 Intel Core i5 1235U Laptop", 45990, "budget", color="Carbon Black")
laptop("Dell", "G15 5530 Intel Core i5 13450HX RTX 3050 Gaming Laptop", 72990, "gaming", color="Dark Shadow Grey")
laptop("Dell", "G15 5530 Intel Core i7 13650HX RTX 4060 Gaming Laptop", 104990, "gaming", color="Dark Shadow Grey")
laptop("Dell", "15 AMD Ryzen 5 7530U Laptop", 45990, "budget", color="Carbon Black")
laptop("Dell", "XPS 13 Intel Core Ultra 7 256V Laptop", 159990, "premium", color="Platinum")
laptop("Lenovo", "IdeaPad Slim 3 Intel Core i3 1315U Laptop", 38990, "budget", color="Arctic Grey")
laptop("Lenovo", "IdeaPad Slim 3 Intel Core i5 13420H Laptop", 56990, color="Arctic Grey")
laptop("Lenovo", "IdeaPad Slim 3 AMD Ryzen 5 7520U Laptop", 41990, "budget", color="Arctic Grey")
laptop("Lenovo", "IdeaPad Slim 5 Intel Core Ultra 5 125H Laptop", 74990, color="Cosmic Blue")
laptop("Lenovo", "IdeaPad Slim 5 AMD Ryzen 7 8845HS Laptop", 79990, color="Cloud Grey")
laptop("Lenovo", "LOQ 15 Intel Core i5 12450HX RTX 3050 Gaming Laptop", 69990, "gaming", color="Luna Grey")
laptop("Lenovo", "LOQ 15 AMD Ryzen 7 7435HS RTX 4060 Gaming Laptop", 94990, "gaming", color="Luna Grey")
laptop("Lenovo", "Legion 5 AMD Ryzen 7 8845HS RTX 4060 Gaming Laptop", 129990, "gaming", color="Luna Grey")
laptop("Lenovo", "Legion Pro 5 Intel Core i9 14900HX RTX 4070 Gaming Laptop", 199990, "gaming", color="Onyx Grey")
laptop("Lenovo", "ThinkPad E14 Intel Core i5 1335U Laptop", 72990, color="Graphite Black")
laptop("Lenovo", "ThinkBook 15 Intel Core i5 1335U Laptop", 59990, color="Mineral Grey")
laptop("Lenovo", "Yoga Slim 7 Intel Core Ultra 7 155H Laptop", 109990, "premium", color="Luna Grey")
laptop("ASUS", "Vivobook 15 Intel Core i3 1215U Laptop", 35990, "budget", color="Quiet Blue")
laptop("ASUS", "Vivobook 15 Intel Core i5 1334U Laptop", 52990, color="Cool Silver")
laptop("ASUS", "Vivobook 16 AMD Ryzen 7 7730U Laptop", 59990, color="Cool Silver")
laptop("ASUS", "Vivobook S14 OLED Intel Core Ultra 5 125H Laptop", 79990, color="Neutral Black")
laptop("ASUS", "TUF Gaming A15 AMD Ryzen 7 7435HS RTX 4050 Laptop", 79990, "gaming", color="Graphite Black")
laptop("ASUS", "TUF Gaming A15 AMD Ryzen 7 7445HS RTX 4060 Laptop", 94990, "gaming", color="Graphite Black")
laptop("ASUS", "TUF Gaming F15 Intel Core i5 11400H RTX 3050 Laptop", 62990, "gaming", color="Graphite Black")
laptop("ASUS", "TUF Gaming F15 Intel Core i7 13620H RTX 4060 Laptop", 99990, "gaming", color="Mecha Gray")
laptop("ASUS", "ROG Strix G16 Intel Core i7 13650HX RTX 4060 Gaming Laptop", 139990, "gaming", color="Eclipse Gray")
laptop("ASUS", "Zenbook 14 OLED Intel Core Ultra 7 155H Laptop", 99990, "premium", color="Ponder Blue")
laptop("ASUS", "ROG Zephyrus G14 AMD Ryzen 9 8945HS RTX 4070 Gaming Laptop", 199990, "premium", color="Eclipse Gray")
laptop("Acer", "Aspire Lite Intel Core i3 1215U Laptop", 30990, "budget", color="Steel Gray")
laptop("Acer", "Aspire Lite AMD Ryzen 5 5625U Laptop", 37990, "budget", color="Steel Gray")
laptop("Acer", "Aspire 7 Intel Core i5 12450H RTX 3050 Gaming Laptop", 57990, "gaming", color="Charcoal Black")
laptop("Acer", "Nitro V Intel Core i5 13420H RTX 4050 Gaming Laptop", 69990, "gaming", color="Obsidian Black")
laptop("Acer", "Nitro V AMD Ryzen 7 7735HS RTX 4060 Gaming Laptop", 89990, "gaming", color="Obsidian Black")
laptop("Acer", "Predator Helios Neo 16 Intel Core i7 14650HX RTX 4060 Gaming Laptop", 129990, "gaming", color="Abyssal Black")
laptop("Acer", "Swift Go 14 Intel Core Ultra 5 125H Laptop", 69990, color="Pure Silver")
laptop("MSI", "Thin 15 Intel Core i5 12450H RTX 4050 Gaming Laptop", 64990, "gaming", color="Cosmos Gray")
laptop("MSI", "Katana 15 Intel Core i7 13620H RTX 4060 Gaming Laptop", 109990, "gaming", color="Black")
laptop("MSI", "Modern 14 Intel Core i5 1235U Laptop", 41990, "budget", color="Classic Black")
laptop("Samsung", "Galaxy Book4 Intel Core i5 1335U Laptop", 64990, color="Gray")
laptop("Samsung", "Galaxy Book5 Pro Intel Core Ultra 7 256V Laptop", 129990, "premium", "2025-03-20", "Gray")


# ---------------------------------------------------------------------------
# Tablets
# ---------------------------------------------------------------------------
def tablet(brand, model, rows, launch=None, color="Grey", markup=1.15):
    for ram, storage, price in rows:
        spec = f"{_st(storage)}" if ram is None else f"{ram} GB RAM, {_st(storage)}"
        mrp = price if brand == "Apple" else _r(price * markup)
        _add(brand, model, spec, "Tablet", mrp, price, color, launch)


tablet("Apple", "iPad 11-inch A16 Wi-Fi", [(None, 128, 34900), (None, 256, 44900), (None, 512, 64900)], "2025-03-12", "Blue")
tablet("Apple", "iPad 11-inch A16 Wi-Fi Cellular", [(None, 128, 49900), (None, 256, 59900)], "2025-03-12", "Blue")
tablet("Apple", "iPad Air 11-inch M3 Wi-Fi", [(None, 128, 59900), (None, 256, 69900), (None, 512, 89900)], "2025-03-12", "Space Grey")
tablet("Apple", "iPad Air 13-inch M3 Wi-Fi", [(None, 128, 79900), (None, 256, 89900), (None, 512, 109900)], "2025-03-12", "Starlight")
tablet("Apple", "iPad Pro 11-inch M5 Wi-Fi", [(None, 256, 99900), (None, 512, 119900), (None, 1024, 159900)], "2025-10-22", "Space Black")
tablet("Apple", "iPad Pro 13-inch M5 Wi-Fi", [(None, 256, 129900), (None, 512, 149900)], "2025-10-22", "Silver")
tablet("Apple", "iPad mini A17 Pro Wi-Fi", [(None, 128, 49900), (None, 256, 59900), (None, 512, 79900)], color="Purple")
tablet("Apple", "iPad 10th Generation Wi-Fi", [(None, 64, 29900), (None, 256, 44900)], color="Silver")
tablet("Samsung", "Galaxy Tab S10 FE Wi-Fi", [(8, 128, 42999), (12, 256, 49999)], "2025-04-03", "Gray")
tablet("Samsung", "Galaxy Tab S10 FE+ Wi-Fi", [(8, 128, 53999), (12, 256, 60999)], "2025-04-03", "Blue")
tablet("Samsung", "Galaxy Tab S10+ Wi-Fi", [(12, 256, 90999), (12, 512, 101999)], color="Moonstone Gray")
tablet("Samsung", "Galaxy Tab S10 Ultra Wi-Fi", [(12, 256, 108999), (12, 512, 119999)], color="Moonstone Gray")
tablet("Samsung", "Galaxy Tab S9 FE Wi-Fi", [(6, 128, 31999), (8, 256, 36999)], color="Gray", markup=1.4)
tablet("Samsung", "Galaxy Tab A9+ Wi-Fi", [(4, 64, 15999), (8, 128, 19999)], color="Graphite", markup=1.3)
tablet("Xiaomi", "Pad 7", [(8, 128, 27999), (12, 256, 30999)], "2025-01-10", "Graphite Gray")
tablet("Redmi", "Pad 2", [(6, 128, 15999), (8, 256, 18999)], "2025-06-24", "Graphite Gray")
tablet("Redmi", "Pad SE", [(4, 128, 11999), (6, 128, 12999)], color="Graphite Gray", markup=1.4)
tablet("OnePlus", "Pad 3", [(12, 256, 47999), (16, 512, 52999)], "2025-07-08", "Storm Blue")
tablet("OnePlus", "Pad 2", [(8, 128, 37999), (12, 256, 41999)], color="Nimbus Gray")
tablet("OnePlus", "Pad Go 2", [(8, 128, 26999), (8, 256, 29999)], "2025-10-01", "Shadow Black")
tablet("Lenovo", "Idea Tab Pro", [(8, 256, 27999), (12, 256, 30999)], "2025-01-20", "Luna Grey")
tablet("Lenovo", "Tab M11", [(4, 128, 13999), (8, 128, 16999)], color="Luna Grey", markup=1.5)
tablet("realme", "Pad 2", [(6, 128, 17999), (8, 256, 21999)], color="Inspiration Green", markup=1.2)


# ---------------------------------------------------------------------------
# Televisions
# ---------------------------------------------------------------------------
def tv(brand, line, sizes: dict, platform, launch=None, markup=1.55):
    for size, price in sizes.items():
        _add(brand, f"{size} inch {line}", platform, "TV", _r(price * markup), price, "Black", launch)


tv("Samsung", "HD Ready Smart LED TV", {32: 13990}, "Tizen")
tv("Samsung", "Crystal 4K Vision Pro UHD Smart LED TV", {43: 27990, 50: 33990, 55: 39990, 65: 59990, 75: 89990}, "Tizen")
tv("Samsung", "QLED 4K Smart TV", {43: 34990, 55: 49990, 65: 74990, 75: 109990}, "Tizen")
tv("Samsung", "Neo QLED 4K Smart TV", {55: 99990, 65: 139990, 75: 199990}, "Tizen")
tv("Samsung", "OLED 4K Smart TV", {55: 149990, 65: 219990}, "Tizen")
tv("LG", "HD Ready Smart LED TV", {32: 13490}, "webOS")
tv("LG", "UHD 4K Smart LED TV UA82", {43: 29990, 50: 35990, 55: 41990, 65: 64990, 75: 94990}, "webOS")
tv("LG", "QNED 4K Smart TV", {50: 44990, 55: 54990, 65: 79990, 75: 119990}, "webOS")
tv("LG", "OLED evo C4 4K Smart TV", {48: 109990, 55: 129990, 65: 189990, 77: 299990}, "webOS")
tv("Sony", "Bravia 2 4K Ultra HD Smart LED Google TV", {43: 37990, 50: 46990, 55: 52990, 65: 76990}, "Google TV")
tv("Sony", "Bravia 3 4K Ultra HD Smart LED Google TV", {55: 61990, 65: 84990, 75: 129990}, "Google TV")
tv("Sony", "Bravia 7 Mini LED 4K Google TV", {55: 139990, 65: 189990}, "Google TV")
tv("Sony", "Bravia 8 OLED 4K Google TV", {55: 179990, 65: 249990}, "Google TV")
tv("Xiaomi", "X Pro QLED 4K Smart Google TV", {43: 29999, 55: 39999, 65: 59999}, "Google TV", markup=1.5)
tv("Xiaomi", "A Series 4K Smart Google TV", {32: 12499, 43: 22999, 50: 27999, 55: 31999}, "Google TV", markup=1.6)
tv("TCL", "C61K QLED 4K Google TV", {43: 26990, 55: 34990, 65: 49990, 75: 74990}, "Google TV", markup=2.2)
tv("TCL", "P7K 4K Ultra HD Google TV", {43: 23990, 50: 27990, 55: 31990}, "Google TV", markup=2.2)
tv("Hisense", "E7Q QLED 4K Smart TV", {43: 25999, 55: 33999, 65: 47999}, "VIDAA", markup=1.9)
tv("Hisense", "A6N 4K Ultra HD Smart TV", {43: 22999, 50: 26999, 55: 29999}, "VIDAA", markup=1.9)
tv("OnePlus", "Y1S Pro 4K Ultra HD Smart Android TV", {43: 25999, 50: 30999, 55: 35999}, "Android TV", markup=1.3)
tv("Vu", "GloLED 4K Smart Google TV", {43: 25999, 50: 29999, 55: 33999, 65: 49999}, "Google TV", markup=1.5)
tv("Vu", "Vibe QLED 4K Smart Google TV", {43: 23999, 55: 31999, 65: 44999}, "Google TV", markup=1.5)
tv("Acer", "Super Series QLED 4K Google TV", {43: 24999, 55: 32999, 65: 49999}, "Google TV", markup=1.8)
tv("Toshiba", "C350NP 4K Ultra HD Smart LED TV", {43: 23999, 55: 33999, 65: 49999}, "VIDAA", markup=1.8)
tv("Thomson", "Phoenix 4K QLED Google TV", {43: 21999, 50: 25999, 55: 29999}, "Google TV", markup=1.6)
tv("Kodak", "CA Pro 4K Ultra HD Smart Android TV", {43: 19999, 50: 23999, 55: 27999}, "Android TV", markup=1.6)
tv("iFFALCON", "U75 4K Ultra HD Smart Google TV", {43: 20999, 55: 28999}, "Google TV", markup=2.0)


# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------
def audio(brand, model, mrp, price, spec="Bluetooth", color="Black", launch=None):
    _add(brand, model, spec, "Audio", mrp, price, color, launch)


# Headphones
audio("Sony", "WH-1000XM6 Wireless Noise Cancelling Headphones", 39990, 37990, launch="2025-05-30")
audio("Sony", "WH-1000XM5 Wireless Noise Cancelling Headphones", 34990, 26990)
audio("Sony", "WH-1000XM4 Wireless Noise Cancelling Headphones", 29990, 19990)
audio("Sony", "WH-CH720N Wireless Noise Cancelling Headphones", 14990, 8990)
audio("Sony", "WH-CH520 Wireless Headphones", 5990, 3990)
audio("Sony", "ULT WEAR Wireless Noise Cancelling Headphones", 24990, 14990)
audio("Bose", "QuietComfort Ultra Wireless Headphones", 45900, 35900)
audio("Bose", "QuietComfort Wireless Headphones", 35900, 25900)
audio("Apple", "AirPods Max USB-C", 59900, 54900, color="Midnight")
audio("JBL", "Tune 770NC Wireless Headphones", 9999, 5999)
audio("JBL", "Tune 520BT Wireless Headphones", 4999, 2999)
audio("JBL", "Live 770NC Wireless Headphones", 14999, 9999)
audio("JBL", "Tour One M2 Wireless Headphones", 24999, 17999)
audio("Sennheiser", "Momentum 4 Wireless Headphones", 34990, 24990)
audio("Sennheiser", "Accentum Plus Wireless Headphones", 19990, 12990)
audio("boAt", "Rockerz 450 Wireless Headphones", 3990, 1299, color="Luscious Black")
audio("boAt", "Rockerz 550 Wireless Headphones", 4999, 1499)
audio("boAt", "Rockerz 480 Wireless Headphones", 4999, 1599)
audio("boAt", "Nirvana 751 ANC Wireless Headphones", 7990, 3999)
audio("Marshall", "Major V Wireless Headphones", 16999, 13999)
audio("Marshall", "Monitor II ANC Wireless Headphones", 37999, 29999)
audio("Soundcore by Anker", "Space One Wireless Headphones", 9999, 7999)
audio("Soundcore by Anker", "Life Q30 Wireless Headphones", 7999, 4999)
audio("Skullcandy", "Crusher Evo Wireless Headphones", 17999, 12999)
audio("Audio-Technica", "ATH-M50x Studio Headphones", 16000, 12999, spec="Wired")
audio("Noise", "Two Wireless Headphones", 3999, 1499)
audio("OnePlus", "Nord Wireless Headphones", 2499, 1999)
# Earbuds
audio("Apple", "AirPods Pro 3", 25900, 25900, color="White", launch="2025-09-19")
audio("Apple", "AirPods Pro (2nd Generation) USB-C", 24900, 20900, color="White")
audio("Apple", "AirPods 4", 12900, 11900, color="White")
audio("Apple", "AirPods 4 with Active Noise Cancellation", 17900, 16900, color="White")
audio("Samsung", "Galaxy Buds3 Pro", 19999, 14999, color="Silver")
audio("Samsung", "Galaxy Buds3", 14999, 9999, color="Silver")
audio("Samsung", "Galaxy Buds FE", 9999, 5999, color="Graphite")
audio("Sony", "WF-1000XM5 Wireless Earbuds", 24990, 17990)
audio("Sony", "WF-C710N Wireless Earbuds", 11990, 7990)
audio("Sony", "WF-C510 Wireless Earbuds", 5990, 3990)
audio("Google", "Pixel Buds Pro 2", 22900, 19900, color="Hazel")
audio("OnePlus", "Buds Pro 3", 11999, 9999, color="Midnight Opus")
audio("OnePlus", "Buds 3", 5499, 4499, color="Metallic Gray")
audio("OnePlus", "Nord Buds 3 Pro", 3299, 2799, color="Starry Black")
audio("OnePlus", "Nord Buds 3", 2299, 1999, color="Harmonic Gray")
audio("Nothing", "Ear (3)", 14999, 14999, color="White", launch="2025-09-18")
audio("Nothing", "Ear", 14999, 11999, color="White")
audio("Nothing", "Ear (a)", 7999, 5999, color="Yellow")
audio("CMF by Nothing", "Buds 2 Plus", 3299, 2799, color="Blue")
audio("CMF by Nothing", "Buds 2", 2999, 2499, color="Dark Grey")
audio("CMF by Nothing", "Buds 2a", 2199, 1999, color="Orange")
audio("boAt", "Airdopes 141 TWS Earbuds", 4490, 1199, color="Bold Black")
audio("boAt", "Airdopes 161 TWS Earbuds", 4490, 1099, color="Pebble Black")
audio("boAt", "Airdopes 131 Pro TWS Earbuds", 3490, 899, color="Active Black")
audio("boAt", "Airdopes 311 Pro TWS Earbuds", 4990, 1299, color="Cyan Cider")
audio("boAt", "Nirvana Ion TWS Earbuds", 4990, 1999, color="Charcoal Black")
audio("Noise", "Buds VS104 TWS Earbuds", 3499, 999, color="Jet Black")
audio("Noise", "Air Buds Pro 3 TWS Earbuds", 4999, 1999, color="Jet Black")
audio("realme", "Buds Air 7 TWS Earbuds", 3999, 3299, color="Ivory Gold")
audio("realme", "Buds T310 TWS Earbuds", 2999, 2199, color="Monet Purple")
audio("JBL", "Tune Beam 2 TWS Earbuds", 6999, 4999)
audio("JBL", "Wave Beam 2 TWS Earbuds", 3999, 2999)
audio("JBL", "Live Beam 3 TWS Earbuds", 19999, 13999)
audio("Soundcore by Anker", "Liberty 4 NC TWS Earbuds", 8999, 5999)
audio("Boult", "Z40 Pro TWS Earbuds", 4499, 1199)
audio("Mivi", "DuoPods K6 TWS Earbuds", 2999, 999)
audio("Jabra", "Elite 8 Active Gen 2 TWS Earbuds", 21999, 15999)
audio("Bose", "QuietComfort Ultra Earbuds", 25900, 21900)
# Speakers
audio("JBL", "Flip 7 Portable Bluetooth Speaker", 14999, 12999, launch="2025-05-15")
audio("JBL", "Flip 6 Portable Bluetooth Speaker", 14999, 9999)
audio("JBL", "Charge 6 Portable Bluetooth Speaker", 19999, 16999, launch="2025-05-15")
audio("JBL", "Charge 5 Portable Bluetooth Speaker", 18999, 14999)
audio("JBL", "Go 4 Portable Bluetooth Speaker", 4999, 3499)
audio("JBL", "Clip 5 Portable Bluetooth Speaker", 6999, 5499)
audio("JBL", "PartyBox 110 Party Speaker", 39999, 29999)
audio("Sony", "ULT Field 1 Portable Bluetooth Speaker", 12990, 9990)
audio("Sony", "SRS-XB100 Portable Bluetooth Speaker", 5990, 3990)
audio("Sony", "ULT Field 3 Portable Bluetooth Speaker", 24990, 18990)
audio("boAt", "Stone 1200F Bluetooth Speaker", 9990, 3499)
audio("boAt", "Stone 350 Bluetooth Speaker", 3490, 1299)
audio("boAt", "PartyPal 390 Party Speaker", 14990, 7999)
audio("Marshall", "Emberton III Portable Bluetooth Speaker", 19999, 16999)
audio("Marshall", "Emberton II Portable Bluetooth Speaker", 16999, 13999)
audio("Marshall", "Willen II Portable Bluetooth Speaker", 9999, 7499)
audio("Bose", "SoundLink Flex Portable Bluetooth Speaker", 17900, 13900)
audio("Bose", "SoundLink Max Portable Bluetooth Speaker", 46900, 39900)
audio("Amazon", "Echo Dot 5th Gen Smart Speaker with Alexa", 5499, 4499, spec="Wi-Fi", color="Charcoal")
audio("Amazon", "Echo Pop Smart Speaker with Alexa", 4999, 3499, spec="Wi-Fi", color="Charcoal")
audio("Apple", "HomePod mini Smart Speaker", 10900, 9900, spec="Wi-Fi", color="Space Grey")
audio("Ultimate Ears", "Wonderboom 4 Portable Bluetooth Speaker", 9999, 7999)
# Soundbars
audio("Sony", "HT-S20R 5.1 Channel Soundbar", 24990, 13990, spec="400 W")
audio("Sony", "HT-S40R 5.1 Channel Soundbar", 34990, 22990, spec="600 W")
audio("Sony", "Bravia Theatre Bar 6 Soundbar", 49990, 39990, spec="350 W")
audio("JBL", "Cinema SB580 3.1 Channel Soundbar", 24999, 17999, spec="440 W")
audio("JBL", "Bar 300 5.0 Channel Soundbar", 39999, 29999, spec="260 W")
audio("Samsung", "HW-B550 2.1 Channel Soundbar", 25990, 14990, spec="410 W")
audio("Samsung", "HW-Q600C 3.1.2 Channel Soundbar", 49990, 32990, spec="360 W")
audio("LG", "S65Q 3.1 Channel Soundbar", 39990, 21990, spec="420 W")
audio("boAt", "Aavante Bar 1160 2.1 Channel Soundbar", 9990, 3999, spec="60 W")
audio("boAt", "Aavante Bar 3150D 5.1 Channel Soundbar", 32990, 12999, spec="300 W")
audio("Polk Audio", "Signa S4 3.1.2 Channel Soundbar", 49990, 29990, spec="Dolby Atmos")
audio("Zebronics", "Juke Bar 9500WS Pro 5.1 Channel Soundbar", 34999, 14999, spec="525 W")


# ---------------------------------------------------------------------------
# Wearables
# ---------------------------------------------------------------------------
def wear(brand, model, rows, launch=None, color="Black"):
    for spec, mrp, price in rows:
        _add(brand, model, spec, "Wearable", mrp, price, color, launch)


wear("Apple", "Watch Series 11 GPS", [("42mm", 46900, 45900), ("46mm", 49900, 48900)], "2025-09-19", "Jet Black")
wear("Apple", "Watch Series 11 GPS Cellular", [("42mm", 56900, 55900), ("46mm", 59900, 58900)], "2025-09-19", "Rose Gold")
wear("Apple", "Watch Ultra 3 GPS Cellular", [("49mm", 89900, 87900)], "2025-09-19", "Natural Titanium")
wear("Apple", "Watch SE 3 GPS", [("40mm", 25900, 25900), ("44mm", 28900, 28900)], "2025-09-19", "Midnight")
wear("Apple", "Watch SE (2nd Gen) GPS", [("40mm", 24900, 22900), ("44mm", 27900, 25900)], color="Midnight")
wear("Apple", "Watch Series 10 GPS", [("42mm", 46900, 39900), ("46mm", 49900, 42900)], color="Jet Black")
wear("Samsung", "Galaxy Watch8 Bluetooth", [("40mm", 32999, 29999), ("44mm", 35999, 32999)], "2025-07-25", "Graphite")
wear("Samsung", "Galaxy Watch8 LTE", [("40mm", 36999, 33999), ("44mm", 39999, 36999)], "2025-07-25", "Silver")
wear("Samsung", "Galaxy Watch8 Classic Bluetooth", [("46mm", 46999, 42999)], "2025-07-25", "Black")
wear("Samsung", "Galaxy Watch Ultra LTE", [("47mm", 59999, 49999)], color="Titanium Gray")
wear("Samsung", "Galaxy Watch7 Bluetooth", [("40mm", 32999, 26999), ("44mm", 35999, 29999)], color="Green")
wear("Samsung", "Galaxy Fit3 Fitness Band", [("1.6 inch", 5999, 3999)], color="Gray")
wear("Google", "Pixel Watch 3 Bluetooth", [("41mm", 39900, 35900), ("45mm", 43900, 39900)], color="Matte Black")
wear("OnePlus", "Watch 3", [("43mm", 24999, 19999)], "2025-02-18", "Emerald Titanium")
wear("Garmin", "Forerunner 265", [("46mm", 49990, 44990)], color="Black")
wear("Garmin", "Forerunner 965", [("47mm", 69990, 62990)], color="Carbon Gray")
wear("Garmin", "Venu 3", [("45mm", 49990, 44990)], color="Slate")
wear("Garmin", "Instinct 2 Solar", [("45mm", 42990, 34990)], color="Graphite")
wear("Amazfit", "Balance", [("46mm", 21999, 17999)], color="Midnight")
wear("Amazfit", "Active 2", [("44mm", 12999, 9999)], "2025-01-15", "Black")
wear("Amazfit", "Bip 6", [("1.97 inch", 8999, 7499)], "2025-04-10", "Charcoal")
wear("Noise", "ColorFit Pro 6 Max", [("1.96 inch", 9999, 5999)], color="Jet Black")
wear("Noise", "ColorFit Ultra 3", [("1.96 inch", 7999, 3499)], color="Jet Black")
wear("boAt", "Wave Sigma 3 Smartwatch", [("2.01 inch", 7999, 1299)], color="Active Black")
wear("boAt", "Storm Infinity Smartwatch", [("1.85 inch", 6999, 1599)], color="Deep Blue")
wear("Fire-Boltt", "Phoenix Ultra Smartwatch", [("1.39 inch", 9999, 1799)], color="Black")
wear("Fitbit", "Charge 6 Fitness Tracker", [("Standard", 14999, 12999)], color="Obsidian")
wear("Xiaomi", "Smart Band 9 Pro", [("1.74 inch", 4999, 3999)], color="Obsidian Black")
wear("Redmi", "Watch 5 Active", [("2 inch", 2999, 2499)], color="Midnight Black")
wear("CMF by Nothing", "Watch Pro 2", [("1.32 inch", 4999, 4499)], color="Ash Grey")


# ---------------------------------------------------------------------------
# Cameras
# ---------------------------------------------------------------------------
def cam(brand, model, spec, mrp, price, launch=None):
    _add(brand, model, spec, "Camera", mrp, price, "Black", launch)


cam("Canon", "EOS R50 Mirrorless Camera", "RF-S 18-45mm Kit", 75995, 67990)
cam("Canon", "EOS R50 Mirrorless Camera", "Body Only", 62995, 57990)
cam("Canon", "EOS R10 Mirrorless Camera", "RF-S 18-45mm Kit", 89995, 79990)
cam("Canon", "EOS R100 Mirrorless Camera", "RF-S 18-45mm Kit", 49995, 44990)
cam("Canon", "EOS 1500D DSLR Camera", "EF-S 18-55mm Kit", 41995, 37990)
cam("Canon", "EOS 200D II DSLR Camera", "EF-S 18-55mm Kit", 61995, 54990)
cam("Canon", "EOS R8 Full Frame Mirrorless Camera", "Body Only", 149995, 134990)
cam("Sony", "ZV-E10 II Mirrorless Vlog Camera", "16-50mm Kit", 99990, 94990)
cam("Sony", "ZV-E10 Mirrorless Vlog Camera", "16-50mm Kit", 69990, 62990)
cam("Sony", "Alpha 6400 Mirrorless Camera", "16-50mm Kit", 85990, 78990)
cam("Sony", "Alpha 7 IV Full Frame Mirrorless Camera", "Body Only", 242990, 214990)
cam("Sony", "ZV-1F Vlog Camera", "Fixed Lens", 52990, 44990)
cam("Nikon", "Z30 Mirrorless Camera", "16-50mm Kit", 60995, 54990)
cam("Nikon", "Z50II Mirrorless Camera", "16-50mm Kit", 103995, 95990, "2024-11-07")
cam("Nikon", "Z5II Full Frame Mirrorless Camera", "Body Only", 155995, 149990, "2025-04-03")
cam("Fujifilm", "X-S20 Mirrorless Camera", "XC 15-45mm Kit", 115999, 104999)
cam("Fujifilm", "X-M5 Mirrorless Camera", "XC 15-45mm Kit", 84999, 79999, "2024-11-14")
cam("GoPro", "HERO13 Black Action Camera", "Standard", 45000, 39990)
cam("GoPro", "HERO12 Black Action Camera", "Standard", 39990, 32990)
cam("DJI", "Osmo Action 5 Pro Action Camera", "Standard Combo", 38990, 35990)
cam("DJI", "Osmo Pocket 3 Gimbal Camera", "Standard", 54990, 49990)
cam("DJI", "Mini 4 Pro Drone", "Fly More Combo", 109990, 99990)
cam("Insta360", "X4 360 Action Camera", "Standard", 54990, 49990)
cam("Insta360", "X5 360 Action Camera", "Standard", 59990, 56990, "2025-04-22")
cam("Insta360", "Ace Pro 2 Action Camera", "Standard", 49990, 44990)


# ---------------------------------------------------------------------------
# Appliances
# ---------------------------------------------------------------------------
def appliance(brand, model, spec, price, markup=1.4, color="Silver", sub=None, launch=None):
    _add(brand, model, spec, "Appliance", _r(price * markup), price, color, launch, sub)


# Air conditioners: brand x tonnage x star rating
AC_LINES = {
    "LG": ("AI Dual Inverter", 1.00), "Voltas": ("Vectra Inverter", 0.92),
    "Daikin": ("Inverter", 1.05), "Samsung": ("Bespoke AI WindFree Inverter", 1.02),
    "Blue Star": ("Inverter", 0.97), "Lloyd": ("Inverter", 0.90),
    "Panasonic": ("Wi-Fi Smart Inverter", 1.04), "Carrier": ("Flexicool Inverter", 0.98),
    "Haier": ("Kinouchi Inverter", 0.93), "Godrej": ("Inverter", 0.88), "Hitachi": ("Kaze Plus Inverter", 1.06),
}
AC_BASE = {1.0: 31990, 1.5: 37990, 2.0: 48990}
for brand, (line, mult) in AC_LINES.items():
    for ton, base in AC_BASE.items():
        for star, prem in ((3, 0), (5, 0.12)):
            t = f"{ton:g}"
            appliance(brand, f"Split AC {t} Ton {star} Star {line}", "Copper Condenser",
                      _r(base * mult * (1 + prem)), markup=1.55, color="White", sub="AC")

# Refrigerators
FRIDGES = [
    ("Samsung", "Single Door 183 L 4 Star", 16490), ("Samsung", "Double Door 236 L 3 Star Frost Free", 24990),
    ("Samsung", "Double Door 253 L 3 Star Convertible", 27490), ("Samsung", "Double Door 322 L 3 Star Convertible", 36990),
    ("Samsung", "Side by Side 653 L Convertible", 82990),
    ("LG", "Single Door 185 L 5 Star", 18490), ("LG", "Double Door 242 L 3 Star Frost Free", 26990),
    ("LG", "Double Door 322 L 3 Star Convertible", 38990), ("LG", "Side by Side 655 L Inverter", 89990),
    ("Whirlpool", "Single Door 184 L 2 Star", 14490), ("Whirlpool", "Double Door 240 L 2 Star Frost Free", 23490),
    ("Whirlpool", "Triple Door 240 L 3 Star", 26990),
    ("Godrej", "Single Door 180 L 2 Star", 13490), ("Godrej", "Double Door 244 L 3 Star Frost Free", 24490),
    ("Haier", "Double Door 240 L 3 Star Frost Free", 23990), ("Haier", "Side by Side 598 L Convertible", 64990),
    ("Bosch", "Double Door 263 L 3 Star Frost Free", 29990), ("Panasonic", "Double Door 268 L 3 Star Frost Free", 28990),
    ("Hisense", "Side by Side 566 L Inverter", 57990), ("Voltas Beko", "Double Door 250 L 3 Star Frost Free", 23490),
]
for brand, model, price in FRIDGES:
    appliance(brand, f"{model} Refrigerator", "Inverter Compressor", price, 1.35)

# Washing machines
WASHERS = [
    ("Samsung", "Front Load 7 kg 5 Star Fully Automatic", 30990), ("Samsung", "Front Load 8 kg 5 Star Fully Automatic", 35990),
    ("Samsung", "Top Load 7 kg 5 Star Fully Automatic", 17990), ("Samsung", "Top Load 9 kg 5 Star Fully Automatic", 22990),
    ("LG", "Front Load 8 kg 5 Star Fully Automatic", 36990), ("LG", "Front Load 9 kg 5 Star Fully Automatic", 41990),
    ("LG", "Top Load 7 kg 5 Star Fully Automatic", 19490), ("LG", "Top Load 8 kg 5 Star Fully Automatic", 21990),
    ("Whirlpool", "Top Load 7.5 kg 5 Star Fully Automatic", 16490), ("Whirlpool", "Semi Automatic 7.5 kg 5 Star", 10490),
    ("IFB", "Front Load 6 kg 5 Star Fully Automatic", 25990), ("IFB", "Front Load 8 kg 5 Star Fully Automatic", 33990),
    ("Bosch", "Front Load 8 kg 5 Star Fully Automatic", 37990), ("Bosch", "Front Load 7 kg 5 Star Fully Automatic", 31990),
    ("Haier", "Top Load 8 kg 5 Star Fully Automatic", 16990), ("Haier", "Front Load 8 kg 5 Star Fully Automatic", 28990),
    ("Godrej", "Top Load 7 kg 5 Star Fully Automatic", 15990), ("Panasonic", "Top Load 8 kg 5 Star Fully Automatic", 19990),
    ("Lloyd", "Front Load 8 kg 5 Star Fully Automatic", 25990), ("Voltas Beko", "Semi Automatic 8 kg 5 Star", 11490),
]
for brand, model, price in WASHERS:
    appliance(brand, f"{model} Washing Machine", "Inverter Motor", price, 1.4, color="Grey")

# Microwaves
MICRO = [
    ("Samsung", "Convection 28 L Microwave Oven", 13490), ("Samsung", "Solo 23 L Microwave Oven", 6490),
    ("LG", "Convection 28 L Microwave Oven", 14490), ("LG", "Solo 20 L Microwave Oven", 5490),
    ("IFB", "Convection 25 L Microwave Oven", 11990), ("Panasonic", "Convection 27 L Microwave Oven", 12990),
    ("Morphy Richards", "Solo 20 L Microwave Oven", 4990), ("Godrej", "Convection 25 L Microwave Oven", 10490),
    ("Bajaj", "Solo 17 L Microwave Oven", 4490), ("Haier", "Convection 30 L Microwave Oven", 13990),
]
for brand, model, price in MICRO:
    appliance(brand, model, "Auto Cook Menu", price, 1.35, color="Black")


# ---------------------------------------------------------------------------
# Monitors
# ---------------------------------------------------------------------------
def monitor(brand, line, sizes: dict, spec, markup=1.5):
    for size, price in sizes.items():
        _add(brand, f"{size} inch {line} Monitor", spec, "Monitor", _r(price * markup), price, "Black")


monitor("LG", "Full HD IPS 100Hz", {24: 7499, 27: 10499}, "HDMI, VGA")
monitor("LG", "UltraGear QHD 180Hz Gaming", {27: 19999, 32: 27999}, "1ms, HDR10")
monitor("LG", "4K UHD IPS", {27: 25999, 32: 34999}, "HDR10, USB-C")
monitor("Samsung", "Full HD IPS 100Hz", {24: 7999, 27: 10999}, "Borderless")
monitor("Samsung", "Odyssey G5 QHD 165Hz Gaming", {27: 21999, 32: 26999}, "Curved, 1ms")
monitor("Samsung", "ViewFinity S8 4K UHD", {27: 29999, 32: 37999}, "HDR10, USB-C")
monitor("Dell", "S Series Full HD IPS 100Hz", {24: 9999, 27: 12999}, "AMD FreeSync")
monitor("Dell", "UltraSharp QHD IPS", {24: 32999, 27: 39999}, "USB-C Hub")
monitor("Dell", "G Series QHD 165Hz Gaming", {27: 22999, 32: 29999}, "1ms, G-Sync")
monitor("BenQ", "GW Full HD IPS Eye-Care", {24: 9490, 27: 12490}, "Low Blue Light")
monitor("BenQ", "MOBIUZ QHD 165Hz Gaming", {27: 29990, 32: 39990}, "HDRi, Speakers")
monitor("Acer", "Nitro Full HD 180Hz Gaming", {24: 8999, 27: 11999}, "0.5ms, FreeSync")
monitor("ASUS", "TUF Gaming Full HD 180Hz", {24: 10499, 27: 13999}, "Fast IPS, ELMB")
monitor("MSI", "MAG QHD 180Hz Gaming", {27: 19999, 32: 25999}, "Rapid IPS")
monitor("Lenovo", "L Series Full HD IPS 100Hz", {24: 8499, 27: 11499}, "Tilt Stand")
monitor("ViewSonic", "VA Full HD 100Hz", {24: 6999, 27: 9499}, "Eye Care")
monitor("Gigabyte", "QHD 170Hz Gaming", {27: 18999, 32: 24999}, "SS IPS, 1ms")
monitor("ZEBRONICS", "Full HD 100Hz LED", {24: 5999, 27: 8499}, "Built-in Speakers")


# ---------------------------------------------------------------------------
# Gaming
# ---------------------------------------------------------------------------
def gaming(brand, model, spec, mrp, price, color="White", launch=None):
    _add(brand, model, spec, "Gaming", mrp, price, color, launch)


gaming("Sony", "PlayStation 5 Slim Console Disc Edition", "1 TB", 54990, 49990)
gaming("Sony", "PlayStation 5 Slim Console Digital Edition", "1 TB", 44990, 39990)
gaming("Sony", "PlayStation 5 Pro Console", "2 TB", 79990, 74990, launch="2024-11-21")
gaming("Sony", "DualSense Wireless Controller for PS5", "Standard", 6390, 5490)
gaming("Sony", "DualSense Edge Wireless Controller", "Pro", 21990, 17990)
gaming("Sony", "PlayStation Portal Remote Player", "Wi-Fi", 18990, 16990)
gaming("Sony", "Pulse 3D Wireless Headset for PS5", "Wireless", 9990, 7990)
gaming("Microsoft", "Xbox Series X Console", "1 TB", 66990, 59990, color="Black")
gaming("Microsoft", "Xbox Series S Console", "512 GB", 37990, 34990)
gaming("Microsoft", "Xbox Series S Console", "1 TB", 44990, 41990, color="Carbon Black")
gaming("Microsoft", "Xbox Wireless Controller", "Standard", 5990, 4990, color="Carbon Black")
gaming("Logitech", "G502 X Plus Wireless Gaming Mouse", "LIGHTSPEED", 17995, 13995, color="Black")
gaming("Logitech", "G Pro X Superlight 2 Gaming Mouse", "Wireless", 16995, 13495, color="Black")
gaming("Razer", "DeathAdder V3 Pro Gaming Mouse", "Wireless", 16999, 12999, color="Black")
gaming("HyperX", "Cloud III Wired Gaming Headset", "Wired", 9990, 6990, color="Black")
gaming("Redragon", "K552 Kumara Mechanical Gaming Keyboard", "Wired", 4999, 2499, color="Black")


# ---------------------------------------------------------------------------
# Accessories & storage
# ---------------------------------------------------------------------------
def acc(brand, model, spec, mrp, price, color="Black", launch=None):
    _add(brand, model, spec, "Accessory", mrp, price, color, launch)


acc("Samsung", "990 PRO NVMe M.2 Internal SSD", "1 TB", 15999, 9999)
acc("Samsung", "990 PRO NVMe M.2 Internal SSD", "2 TB", 27999, 17999)
acc("Samsung", "990 EVO Plus NVMe M.2 Internal SSD", "1 TB", 10999, 7499)
acc("Samsung", "T7 Portable SSD", "1 TB", 14999, 9499, color="Titan Gray")
acc("Samsung", "T7 Portable SSD", "2 TB", 26999, 16999, color="Titan Gray")
acc("WD", "Black SN850X NVMe M.2 Internal SSD", "1 TB", 14999, 8999)
acc("WD", "Elements Portable External Hard Drive", "2 TB", 8999, 6299)
acc("WD", "My Passport Portable External Hard Drive", "4 TB", 14999, 10499)
acc("Crucial", "P3 Plus NVMe M.2 Internal SSD", "1 TB", 9999, 6499)
acc("Crucial", "X9 Pro Portable SSD", "1 TB", 13999, 8499)
acc("SanDisk", "Extreme Portable SSD", "1 TB", 15999, 8999)
acc("SanDisk", "Ultra Dual Drive USB Type-C Pen Drive", "128 GB", 1999, 899)
acc("SanDisk", "Extreme microSDXC Memory Card", "256 GB", 5999, 2499)
acc("Seagate", "Expansion Portable External Hard Drive", "2 TB", 8999, 6499)
acc("Seagate", "One Touch Portable External Hard Drive", "5 TB", 17999, 12999)
acc("Kingston", "NV3 NVMe M.2 Internal SSD", "1 TB", 8999, 5999)
acc("Logitech", "MX Master 3S Wireless Mouse", "Bluetooth", 10995, 8995, color="Graphite")
acc("Logitech", "MX Keys S Wireless Keyboard", "Bluetooth", 13995, 11495, color="Graphite")
acc("Logitech", "M331 Silent Plus Wireless Mouse", "USB Receiver", 1495, 899)
acc("Logitech", "MK270 Wireless Keyboard and Mouse Combo", "USB Receiver", 2295, 1495)
acc("Logitech", "Pebble Mouse 2 M350s", "Bluetooth", 1995, 1295, color="Graphite")
acc("Logitech", "C920 HD Pro Webcam", "1080p", 9995, 6495)
acc("HP", "Smart Tank 580 All-in-One Ink Tank Printer", "Wi-Fi", 18999, 13999, color="White")
acc("Canon", "PIXMA G3770 All-in-One Ink Tank Printer", "Wi-Fi", 19995, 14999)
acc("Epson", "EcoTank L3250 All-in-One Ink Tank Printer", "Wi-Fi", 18999, 14499)
acc("Brother", "HL-L2321D Monochrome Laser Printer", "USB", 14999, 10999)
acc("TP-Link", "Archer AX23 AX1800 Wi-Fi 6 Router", "Dual Band", 6999, 4499)
acc("TP-Link", "Deco X20 AX1800 Mesh Wi-Fi 6 System", "2-Pack", 16999, 11999, color="White")
acc("TP-Link", "Archer C6 AC1200 Wi-Fi Router", "Dual Band", 3999, 2199)
acc("Xiaomi", "Power Bank 4i 20000mAh 33W", "USB-C PD", 2999, 1999)
acc("Ambrane", "Power Bank 20000mAh 22.5W", "USB-C PD", 2999, 1299)
acc("Anker", "Nano Power Bank 10000mAh 30W", "USB-C PD", 5999, 3999)
acc("Apple", "20W USB-C Power Adapter", "USB-C", 1900, 1599, color="White")
acc("Apple", "Pencil Pro", "Bluetooth", 11900, 11500, color="White")
acc("Apple", "AirTag", "1 Pack", 3490, 2999, color="White")
acc("Apple", "AirTag", "4 Pack", 11900, 10499, color="White")
acc("Apple", "Magic Keyboard for iPad Air 11-inch M3", "English", 26900, 26900, color="White", launch="2025-03-12")
acc("Samsung", "25W USB-C Power Adapter", "USB-C", 1999, 1299, color="White")
acc("Amazon", "Kindle Paperwhite 12th Gen E-reader", "16 GB", 17999, 16999)
acc("Amazon", "Fire TV Stick 4K Streaming Device", "Wi-Fi 6", 6999, 4499)
acc("Amazon", "Echo Show 5 3rd Gen Smart Display", "Wi-Fi", 9999, 7499, color="Charcoal")
acc("Google", "Chromecast with Google TV 4K", "Wi-Fi", 6999, 5499, color="Snow")
acc("Portronics", "Toad 23 Wireless Mouse", "USB Receiver", 999, 349)
acc("Zebronics", "Zeb-Transformer Gaming Keyboard and Mouse Combo", "Wired", 2999, 1199)
acc("Qubo", "Smart Home Security Wi-Fi Camera 360", "1080p", 4990, 1999, color="White")
acc("Mi", "360 Home Security Camera 2K", "Wi-Fi", 4999, 2999, color="White")


# ---------------------------------------------------------------------------
# More appliances: window ACs, kitchen and home
# ---------------------------------------------------------------------------
for brand, mult in (("Voltas", 0.95), ("LG", 1.03), ("Blue Star", 1.0), ("Lloyd", 0.93),
                    ("Carrier", 1.0), ("Godrej", 0.92)):
    for ton, base in ((1.0, 27990), (1.5, 32990)):
        for star, prem in ((3, 0), (5, 0.12)):
            appliance(brand, f"Window AC {ton:g} Ton {star} Star Inverter", "Copper Condenser",
                      _r(base * mult * (1 + prem)), markup=1.5, color="White", sub="AC")

HOME = [
    ("Philips", "Air Fryer HD9252 4.1 L", "1400 W", 6999), ("Philips", "Air Fryer XXL HD9285 7.2 L", "2000 W", 14999),
    ("Inalsa", "Air Fryer Tasty Fry 4.2 L", "1400 W", 3999), ("Prestige", "Air Fryer PAF 6.0 4.2 L", "1200 W", 4499),
    ("Havells", "Air Fryer Prolife Digi 4 L", "1230 W", 5999), ("Kent", "Air Fryer Classic 4 L", "1300 W", 4799),
    ("Philips", "Mixer Grinder HL7756 750 W", "3 Jars", 3699), ("Prestige", "Mixer Grinder Iris 750 W", "4 Jars", 3299),
    ("Bajaj", "Mixer Grinder Rex 500 W", "3 Jars", 2199), ("Sujata", "Mixer Grinder Dynamix 900 W", "3 Jars", 5999),
    ("Butterfly", "Mixer Grinder Jet Elite 750 W", "4 Jars", 3199), ("Preethi", "Mixer Grinder Zodiac 750 W", "5 Jars", 7999),
    ("Kent", "RO Water Purifier Grand Plus 8 L", "RO+UV+UF", 15999), ("Aquaguard", "RO Water Purifier Aura 7 L", "RO+UV+MTDS", 13999),
    ("Livpure", "RO Water Purifier Glo Star 7 L", "RO+UV", 9999), ("Pureit", "RO Water Purifier Eco Water Saver 10 L", "RO+UV+MF", 14999),
    ("Havells", "RO Water Purifier Fab Alkaline 7 L", "RO+UV", 16999), ("Kent", "Supreme Extra RO Water Purifier 8 L", "RO+UF", 12999),
    ("Eureka Forbes", "Robot Vacuum Cleaner Forbes LVAC Voice", "Mop", 17999), ("Dreame", "Robot Vacuum Cleaner D10 Plus Gen 2", "Self Empty", 29999),
    ("Xiaomi", "Robot Vacuum Cleaner S20", "Mop", 19999), ("Dyson", "Cordless Vacuum Cleaner V12 Detect Slim", "Laser", 52900),
    ("Philips", "Wet and Dry Vacuum Cleaner PowerPro FC9352", "1900 W", 8999), ("Agaro", "Wet and Dry Vacuum Cleaner Ace 21 L", "1600 W", 6299),
    ("Havells", "Storage Water Heater Monza EC 15 L", "5 Star", 8999), ("AO Smith", "Storage Water Heater HSE-VAS 15 L", "5 Star", 9999),
    ("Bajaj", "Storage Water Heater New Shakti 15 L", "4 Star", 6499), ("Racold", "Storage Water Heater Pronto Neo 3 L", "Instant", 3699),
    ("Crompton", "Storage Water Heater Arno Neo 25 L", "5 Star", 7999), ("V-Guard", "Storage Water Heater Victo 15 L", "5 Star", 7299),
    ("Philips", "Air Purifier AC1715", "HEPA", 12999), ("Sharp", "Air Purifier FP-J40M", "HEPA", 11499),
    ("Coway", "Air Purifier AirMega 150", "HEPA", 11999), ("Xiaomi", "Smart Air Purifier 4 Lite", "HEPA", 9999),
    ("Atomberg", "BLDC Ceiling Fan Renesa 1200 mm", "Remote", 3999), ("Havells", "BLDC Ceiling Fan Stealth Air 1200 mm", "Remote", 5999),
    ("Crompton", "BLDC Ceiling Fan Energion HS 1200 mm", "Remote", 3299), ("Orient", "BLDC Ceiling Fan Aeroquiet 1200 mm", "Remote", 4999),
    ("Philips", "Dry Iron GC1905", "1440 W", 999), ("Morphy Richards", "OTG Oven 40 L Besta", "1600 W", 8999),
    ("Pigeon", "Induction Cooktop Favourite IC 1800 W", "Push Button", 1999), ("Prestige", "Induction Cooktop PIC 20 1600 W", "Push Button", 2499),
    ("Philips", "Electric Kettle HD9306 1.5 L", "1800 W", 1299), ("Kent", "Electric Kettle 1.8 L", "1500 W", 1099),
    ("Faber", "Kitchen Chimney 60 cm Hood Zenith", "1350 m3/hr", 13999), ("Elica", "Kitchen Chimney 60 cm Filterless", "1200 m3/hr", 15999),
    ("Bosch", "Dishwasher Series 4 13 Place Settings", "Free Standing", 39990), ("IFB", "Dishwasher Neptune VX Plus 12 Place Settings", "Free Standing", 31990),
    ("LG", "Dishwasher 14 Place Settings QuadWash", "Free Standing", 44990), ("Voltas Beko", "Dishwasher 14 Place Settings", "Free Standing", 31990),
]
for brand, model, spec, price in HOME:
    appliance(brand, model, spec, price, 1.45, color="Black")

for brand, model, price in [
    ("Samsung", "Double Door 256 L 3 Star Bespoke AI", 30990), ("LG", "Double Door 272 L 3 Star Smart Inverter", 31990),
    ("Whirlpool", "Double Door 265 L 3 Star Intellifresh", 27990), ("Godrej", "Side by Side 564 L Convertible", 55990),
    ("Haier", "Single Door 190 L 4 Star", 15490), ("LG", "Double Door 340 L 3 Star Convertible", 42990),
    ("Samsung", "Triple Door 385 L 3 Star Convertible", 49990), ("Bosch", "Side by Side 580 L Convertible", 74990),
]:
    appliance(brand, f"{model} Refrigerator", "Inverter Compressor", price, 1.35)

# More TVs (extra sizes / lines)
tv("Samsung", "Vision AI QLED 4K Smart TV", {50: 54990, 55: 59990, 65: 84990}, "Tizen", launch="2025-04-09")
tv("LG", "UHD 4K Smart LED TV UT80", {43: 31990, 55: 44990, 65: 66990}, "webOS")
tv("Xiaomi", "FX Pro QLED 4K Smart Fire TV", {43: 26999, 50: 31999, 55: 36999}, "Fire TV OS")
tv("TCL", "QD-Mini LED 4K Google TV Q6C", {55: 49990, 65: 69990, 75: 99990}, "Google TV", launch="2025-05-20", markup=2.0)
tv("Haier", "M95E QLED 4K Google TV", {43: 25990, 55: 34990, 65: 49990}, "Google TV", markup=1.9)
tv("Panasonic", "MX750 4K Ultra HD Smart Google TV", {43: 31990, 55: 42990}, "Google TV", markup=1.6)

# Wired earphones and extra audio
audio("boAt", "Bassheads 100 Wired Earphones", 999, 399, spec="3.5mm")
audio("boAt", "Bassheads 242 Wired Earphones", 1490, 499, spec="3.5mm")
audio("JBL", "C100SI Wired Earphones", 1299, 599, spec="3.5mm")
audio("Sony", "MDR-EX15AP Wired Earphones", 1290, 699, spec="3.5mm")
audio("Apple", "EarPods USB-C", 1900, 1799, spec="USB-C", color="White")
audio("Samsung", "Type-C Wired Earphones", 1499, 799, spec="USB-C", color="White")
audio("realme", "Buds Wireless 5 ANC Neckband", 2499, 1799)
audio("OnePlus", "Bullets Wireless Z2 Neckband", 2299, 1799, color="Magico Black")
audio("boAt", "Rockerz 255 Pro+ Neckband", 3990, 1099, color="Active Black")
audio("JBL", "Tune 215BT Neckband", 2999, 1999)

# More smartphones
phone("Samsung", "Galaxy S24 Ultra", [(12, 1024, 129999)], color="Titanium Gray", markup=1.3)
phone("Samsung", "Galaxy A55 5G", [(8, 128, 33999), (8, 256, 36999)], color="Awesome Iceblue", markup=1.3)
phone("Samsung", "Galaxy A35 5G", [(8, 128, 26999), (8, 256, 29999)], color="Awesome Navy", markup=1.3)
phone("Samsung", "Galaxy M35 5G", [(6, 128, 15999), (8, 128, 17999), (8, 256, 20999)], color="Moonlight Blue", markup=1.3)
phone("vivo", "V40", [(8, 128, 34999), (8, 256, 36999), (12, 512, 41999)], color="Ganges Blue", markup=1.15)
phone("vivo", "T3 Ultra 5G", [(8, 128, 31999), (8, 256, 33999)], color="Lunar Gray", markup=1.2)
phone("OPPO", "Reno13 5G", [(8, 128, 37999), (8, 256, 39999)], "2025-01-09", "Ivory White", 1.1)
phone("OPPO", "Reno13 Pro 5G", [(12, 256, 49999), (12, 512, 54999)], "2025-01-09", "Mist Lavender", 1.1)
phone("realme", "14 Pro+ 5G", [(8, 128, 29999), (8, 256, 31999), (12, 256, 34999)], "2025-01-16", "Pearl White", 1.12)
phone("realme", "GT 6", [(8, 256, 40999), (12, 256, 42999)], color="Fluid Silver", markup=1.2)
phone("Poco", "F6 5G", [(8, 256, 29999), (12, 256, 31999), (12, 512, 33999)], color="Titanium", markup=1.2)
phone("iQOO", "12 5G", [(12, 256, 49999), (16, 512, 54999)], color="Legend", markup=1.2)
phone("Motorola", "Edge 50 Fusion", [(8, 128, 21999), (12, 256, 23999)], color="Marshmallow Blue", markup=1.2)
phone("Motorola", "G05", [(4, 64, 6999)], "2025-01-07", "Plum Red", 1.2)
phone("Lava", "Storm 5G", [(8, 128, 13499)], color="Thunder Black", markup=1.2)
