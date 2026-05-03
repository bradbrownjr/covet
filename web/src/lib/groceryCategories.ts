export interface GroceryCategory {
    slug: string;
    label: string;
}

export const GROCERY_CATEGORIES: GroceryCategory[] = [
    { slug: 'alcohol',            label: 'Alcohol' },
    { slug: 'bakery',             label: 'Bakery' },
    { slug: 'beverages',          label: 'Beverages' },
    { slug: 'bread',              label: 'Bread' },
    { slug: 'breakfast-cereal',   label: 'Breakfast & Cereal' },
    { slug: 'canned-pantry',      label: 'Canned & Pantry' },
    { slug: 'cleaning-household', label: 'Cleaning & Household' },
    { slug: 'condiments-spices',  label: 'Condiments & Spices' },
    { slug: 'dairy-eggs',         label: 'Dairy & Eggs' },
    { slug: 'deli',               label: 'Deli' },
    { slug: 'frozen',             label: 'Frozen' },
    { slug: 'health-beauty',      label: 'Health & Beauty' },
    { slug: 'meat-seafood',       label: 'Meat & Seafood' },
    { slug: 'pasta-grains',       label: 'Pasta & Grains' },
    { slug: 'pet-supplies',       label: 'Pet Supplies' },
    { slug: 'produce',            label: 'Produce' },
    { slug: 'snacks',             label: 'Snacks' },
];
