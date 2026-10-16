"""
Initial menu data for Crunch & Crave.

Loaded into the database by migration 0003. After that, manage
everything from the Django admin (/admin/) — this file is not read
at runtime.
"""

IMG = "https://images.unsplash.com/photo-{}?auto=format&fit=crop&w=1200&q=85"


CATEGORIES = [
    # slug, name, tagline, image id
    ("burgers", "Burgers", "Juicy & loaded", "1568901346375-23c9450c58cd"),
    ("pizza", "Pizza", "Hot & cheesy", "1574071318508-1cdbab80d002"),
    ("chicken", "Chicken", "Crispy & tender", "1562967914-608f82629710"),
    ("fries", "Fries", "Crispy & golden", "1573080496219-bb080dd4f877"),
    ("shawarmas", "Shawarmas", "Wrapped & saucy", "1529006557810-274b9b2fc783"),
    ("parathas", "Parathas", "Flaky & buttery", "1601050690117-94f5f6fa8bd7"),
    ("drinks", "Drinks", "Ice cold", "1513558161293-cdaf765ed2fd"),
    ("combos", "Combos", "Best value", "1550317138-10000687a72b"),
]


# slug: (category, name, price, old_price, rating, reviews, sold, badge,
#        image id, description, ingredients)
PRODUCTS = {
    # BURGERS
    "classic-chicken-burger": ("burgers", "Classic Chicken Burger", 499, 599, 4.8, 96, "300+", "Popular", "1568901346375-23c9450c58cd",
        "A juicy crispy chicken fillet layered with fresh lettuce, creamy mayo and our signature Crave sauce.",
        "Crispy Chicken, Fresh Lettuce, Mayo, Crave Special Sauce, Soft Burger Bun"),
    "zinger-burger": ("burgers", "Zinger Burger", 599, 699, 4.9, 128, "500+", "Best Seller", "1571091718767-18b5b1457add",
        "Our signature crispy zinger burger with spicy chicken fillet, fresh vegetables and creamy sauce.",
        "Crispy Zinger Chicken, Lettuce, Mayo, Spicy Sauce, Burger Bun"),
    "cheese-burger": ("burgers", "Cheese Burger", 549, 649, 4.8, 87, "350+", "Popular", "1550547660-d9450f859349",
        "A delicious chicken burger topped with melted cheese and our creamy signature sauce.",
        "Chicken Patty, Cheddar Cheese, Lettuce, Mayo, Signature Sauce"),
    "double-cheese-burger": ("burgers", "Double Cheese Burger", 749, 849, 4.9, 76, "250+", "Hot", "1606755962773-d324e0a13086",
        "Two juicy chicken patties loaded with double melted cheese for an extra cheesy experience.",
        "2 Chicken Patties, Double Cheese, Lettuce, Mayo, Special Sauce"),
    "chicken-jalapeno-burger": ("burgers", "Chicken Jalapeno Burger", 649, 749, 4.8, 61, "200+", "Hot", "1594212699903-ec8a3eca50f5",
        "Crispy chicken combined with spicy jalapenos and creamy cheese sauce.",
        "Chicken Fillet, Jalapenos, Cheese, Lettuce, Mayo"),
    "bbq-chicken-burger": ("burgers", "BBQ Chicken Burger", 649, 749, 4.8, 54, "180+", "New", "1550317138-10000687a72b",
        "Tender chicken fillet coated with smoky BBQ sauce and fresh vegetables.",
        "Chicken Fillet, BBQ Sauce, Lettuce, Onion, Mayo"),
    "crispy-chicken-burger": ("burgers", "Crispy Chicken Burger", 579, 679, 4.7, 48, "150+", "Popular", "1565299507177-b0ac66763828",
        "Golden crispy chicken fillet served with fresh lettuce and creamy house sauce.",
        "Crispy Chicken, Lettuce, Mayo, Special Sauce, Bun"),
    "mushroom-cheese-burger": ("burgers", "Mushroom Cheese Burger", 699, 799, 4.8, 43, "130+", "New", "1572802419224-296b0aeee0d9",
        "A premium chicken burger topped with sauteed mushrooms and melted cheese.",
        "Chicken Patty, Mushrooms, Cheese, Lettuce, Mayo"),
    "crave-special-burger": ("burgers", "Crave Special Burger", 799, 999, 4.9, 128, "500+", "Best Seller", "1568901346375-23c9450c58cd",
        "Our ultimate signature burger made with premium crispy chicken, double cheese and Crave special sauce.",
        "Premium Chicken, Double Cheese, Lettuce, Jalapenos, Crave Special Sauce"),
    "double-patty-burger": ("burgers", "Double Patty Burger", 749, 849, 4.8, 69, "220+", "Hot", "1572802419224-296b0aeee0d9",
        "Two delicious chicken patties stacked with fresh vegetables and creamy sauce.",
        "2 Chicken Patties, Lettuce, Cheese, Mayo, Special Sauce"),

    # PIZZA
    "chicken-tikka-pizza": ("pizza", "Chicken Tikka Pizza", 999, 1199, 4.8, 91, "400+", "Popular", "1574071318508-1cdbab80d002",
        "Loaded with juicy chicken tikka, mozzarella cheese and our signature pizza sauce.",
        "Chicken Tikka, Mozzarella Cheese, Capsicum, Onion, Pizza Sauce"),
    "chicken-fajita-pizza": ("pizza", "Chicken Fajita Pizza", 1049, 1249, 4.8, 82, "350+", "Popular", "1565299624946-b28f40a0ae38",
        "A delicious combination of fajita chicken, peppers, onions and melted mozzarella.",
        "Fajita Chicken, Capsicum, Onion, Mozzarella, Pizza Sauce"),
    "chicken-achari-pizza": ("pizza", "Chicken Achari Pizza", 1049, 1199, 4.7, 57, "200+", "Hot", "1579751626657-72bc17010498",
        "Spicy achari chicken pizza with a bold Pakistani-inspired flavor.",
        "Achari Chicken, Mozzarella, Onion, Capsicum, Achari Sauce"),
    "chicken-supreme-pizza": ("pizza", "Chicken Supreme Pizza", 1149, 1349, 4.9, 103, "450+", "Best Seller", "1593560708920-61dd98c46a4e",
        "A loaded supreme pizza packed with chicken, cheese and fresh toppings.",
        "Chicken, Cheese, Capsicum, Onion, Olives, Mushrooms"),
    "bbq-chicken-pizza": ("pizza", "BBQ Chicken Pizza", 1099, 1299, 4.8, 74, "280+", "Hot", "1571407970349-bc81e7e96d47",
        "Smoky BBQ chicken combined with mozzarella cheese and fresh vegetables.",
        "BBQ Chicken, Mozzarella, Onion, Capsicum, BBQ Sauce"),
    "cheese-lover-pizza": ("pizza", "Cheese Lover Pizza", 1099, 1249, 4.9, 88, "300+", "Popular", "1574071318508-1cdbab80d002",
        "A cheesy dream made with multiple layers of rich melted cheese.",
        "Mozzarella, Cheddar, Cheese Sauce, Pizza Sauce"),
    "pepperoni-pizza": ("pizza", "Pepperoni Pizza", 1199, 1399, 4.8, 62, "180+", "New", "1628840042765-356cda07504e",
        "Classic pepperoni pizza with generous mozzarella and rich tomato sauce.",
        "Pepperoni, Mozzarella, Tomato Sauce"),
    "malai-boti-pizza": ("pizza", "Malai Boti Pizza", 1149, 1349, 4.9, 71, "250+", "Special", "1579751626657-72bc17010498",
        "Creamy malai boti chicken combined with cheese for a rich and flavorful pizza.",
        "Malai Boti Chicken, Mozzarella, Creamy Sauce, Onion"),

    # CHICKEN
    "crispy-chicken": ("chicken", "Crispy Chicken", 449, 549, 4.8, 74, "250+", "Popular", "1562967914-608f82629710",
        "Golden crispy chicken pieces seasoned with our signature spices.",
        "Chicken, Crispy Coating, Signature Spices"),
    "chicken-strips": ("chicken", "Chicken Strips", 399, 499, 4.7, 58, "200+", "Popular", "1562967916-eb82221dfb92",
        "Tender strips of chicken coated in a crispy golden crust.",
        "Chicken Breast, Crispy Coating, Spices"),
    "chicken-nuggets": ("chicken", "Chicken Nuggets", 349, 449, 4.7, 51, "180+", "Popular", "1562967914-608f82629710",
        "Crunchy bite-sized chicken nuggets perfect for sharing.",
        "Chicken, Crispy Coating, Spices"),
    "chicken-wings": ("chicken", "Chicken Wings", 499, 599, 4.8, 63, "220+", "Hot", "1527477396000-e27163b481c2",
        "Crispy juicy chicken wings tossed in our delicious signature seasoning.",
        "Chicken Wings, Spices, Signature Sauce"),

    # FRIES
    "plain-fries": ("fries", "Plain Fries", 249, 299, 4.6, 41, "150+", "Popular", "1573080496219-bb080dd4f877",
        "Fresh golden crispy fries served hot and perfectly seasoned.",
        "Potatoes, Salt, Seasoning"),
    "masala-fries": ("fries", "Masala Fries", 299, 349, 4.7, 49, "180+", "Hot", "1630384060421-cb20d0e0649d",
        "Crispy fries covered with our special spicy masala seasoning.",
        "Potatoes, Special Masala, Salt"),
    "cheese-fries": ("fries", "Cheese Fries", 399, 449, 4.8, 57, "200+", "Popular", "1585109649139-366815a0d713",
        "Crispy fries covered with creamy melted cheese sauce.",
        "Fries, Cheese Sauce, Cheddar Cheese"),
    "loaded-cheese-fries": ("fries", "Loaded Cheese Fries", 499, 599, 4.9, 67, "250+", "Best Seller", "1585109649139-366815a0d713",
        "Loaded fries topped with cheese, chicken and our special sauces.",
        "Fries, Chicken, Cheese, Mayo, Special Sauce"),

    # SHAWARMAS
    "chicken-shawarma": ("shawarmas", "Chicken Shawarma", 299, 349, 4.8, 86, "350+", "Popular", "1529006557810-274b9b2fc783",
        "Tender chicken shawarma wrapped with fresh vegetables and creamy garlic sauce.",
        "Chicken, Pita, Lettuce, Garlic Sauce, Pickles"),
    "zinger-shawarma": ("shawarmas", "Zinger Shawarma", 399, 449, 4.9, 72, "280+", "Best Seller", "1542574271-7f3b92e6c821",
        "Crispy zinger chicken wrapped in a soft shawarma bread with signature sauces.",
        "Zinger Chicken, Bread, Lettuce, Garlic Mayo, Sauce"),
    "cheese-shawarma": ("shawarmas", "Cheese Shawarma", 399, 449, 4.8, 55, "190+", "Popular", "1561651823-34feb02250e4",
        "Juicy chicken shawarma loaded with melted cheese and creamy sauce.",
        "Chicken, Cheese, Lettuce, Garlic Mayo, Pickles"),

    # PARATHAS
    "chicken-paratha": ("parathas", "Chicken Paratha", 349, 399, 4.7, 52, "180+", "Popular", "1601050690597-df0568f70950",
        "Crispy layered paratha filled with flavorful chicken and special spices.",
        "Paratha, Chicken, Onion, Spices, Sauce"),
    "zinger-paratha": ("parathas", "Zinger Paratha", 449, 499, 4.8, 63, "220+", "Best Seller", "1601050690117-94f5f6fa8bd7",
        "Crispy zinger chicken wrapped inside a buttery flaky paratha.",
        "Zinger Chicken, Paratha, Lettuce, Mayo, Sauce"),
    "cheese-paratha": ("parathas", "Cheese Paratha", 399, 449, 4.8, 47, "160+", "Popular", "1596797038530-2c107229654b",
        "Crispy golden paratha stuffed with rich melted cheese.",
        "Paratha, Mozzarella Cheese, Cheddar Cheese"),

    # DRINKS
    "coca-cola": ("drinks", "Coca Cola", 120, 150, 4.6, 32, "500+", "Popular", "1629203849820-fdd70d49c38e",
        "Refreshing chilled Coca Cola served ice cold.",
        "Carbonated Soft Drink"),
    "pepsi": ("drinks", "Pepsi", 120, 150, 4.6, 29, "450+", "Popular", "1629203851122-3726ecdf080e",
        "Refreshing chilled Pepsi served ice cold.",
        "Carbonated Soft Drink"),
    "mint-margarita": ("drinks", "Mint Margarita", 299, 349, 4.9, 81, "300+", "Best Seller", "1513558161293-cdaf765ed2fd",
        "A refreshing blend of mint, lemon and ice for the perfect cool drink.",
        "Fresh Mint, Lemon, Sugar, Ice"),
    "oreo-shake": ("drinks", "Oreo Shake", 399, 449, 4.9, 73, "250+", "Popular", "1572490122747-3968b75cc699",
        "Creamy Oreo milkshake blended with rich chocolate and crushed cookies.",
        "Milk, Oreo Cookies, Ice Cream, Chocolate"),

    # COMBOS
    "zinger-burger-fries-drink": ("combos", "Zinger Burger + Fries + Drink", 749, 899, 4.9, 112, "500+", "Best Deal", "1571091718767-18b5b1457add",
        "A complete meal featuring our famous Zinger Burger, crispy fries and a chilled drink.",
        "Zinger Burger, Fries, Soft Drink"),
    "pizza-2-drinks": ("combos", "Pizza + 2 Drinks", 1299, 1499, 4.9, 84, "300+", "Best Deal", "1565299624946-b28f40a0ae38",
        "Choose your favorite pizza and enjoy it with two refreshing chilled drinks.",
        "Pizza, 2 Soft Drinks"),
    "crave-mega-deal": ("combos", "Crave Mega Deal", 1999, 2399, 5.0, 146, "600+", "Mega Deal", "1550317138-10000687a72b",
        "The ultimate Crunch & Crave feast packed with burgers, fries, drinks and delicious sides.",
        "Burgers, Fries, Chicken, Drinks, Special Sauces"),
}


FEATURED = [
    "crave-special-burger", "zinger-burger", "chicken-supreme-pizza", "loaded-cheese-fries",
    "chicken-wings", "zinger-shawarma", "mint-margarita", "crave-mega-deal",
]

OFFERS = [
    "zinger-burger", "double-cheese-burger", "crave-special-burger", "chicken-supreme-pizza",
    "cheese-lover-pizza", "zinger-burger-fries-drink", "pizza-2-drinks", "crave-mega-deal",
]

PROMO_CODES = [
    # code, description, percent, min order, max discount
    ("CRAVE10", "10% off any order", 10, 0, 500),
    ("WELCOME20", "20% off orders above Rs. 1,500", 20, 1500, 800),
]

REVIEWS = [
    # name, rating, title, comment, product slug
    ("Ahmed Khan", 5, "Best burger in town", "Honestly one of the best burgers I've had. Everything was fresh and the flavor was amazing!", "crave-special-burger"),
    ("Sarah Ali", 5, "Perfect pizza", "The pizza was absolutely delicious! Perfect cheese, perfect crust and super fast delivery.", "chicken-supreme-pizza"),
    ("Hassan R.", 5, "My new favourite", "Amazing food and amazing service. Crunch & Crave has definitely become my favorite!", None),
    ("Ayesha M.", 4, "Great value combo", "The Zinger combo is great value. Fries were crispy and the drink was ice cold.", "zinger-burger-fries-drink"),
    ("Bilal S.", 5, "Shawarma on point", "Zinger shawarma is unreal. Garlic sauce is exactly how it should be.", "zinger-shawarma"),
    ("Fatima Z.", 5, "Fast and hot", "Ordered at night, arrived in 25 minutes and still piping hot. Will order again.", None),
]
