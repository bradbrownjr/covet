export interface GroceryCategory {
    slug: string;
    label: string;
}

export const GROCERY_CATEGORIES: GroceryCategory[] = [
    { slug: 'produce',            label: 'Produce' },
    { slug: 'bread',              label: 'Bread' },
    { slug: 'bakery',             label: 'Bakery' },
    { slug: 'meat-seafood',       label: 'Meat & Seafood' },
    { slug: 'deli',               label: 'Deli' },
    { slug: 'dairy-eggs',         label: 'Dairy & Eggs' },
    { slug: 'frozen',             label: 'Frozen' },
    { slug: 'canned-pantry',      label: 'Canned & Pantry' },
    { slug: 'pasta-grains',       label: 'Pasta & Grains' },
    { slug: 'snacks',             label: 'Snacks' },
    { slug: 'beverages',          label: 'Beverages' },
    { slug: 'breakfast-cereal',   label: 'Breakfast & Cereal' },
    { slug: 'condiments-spices',  label: 'Condiments & Spices' },
    { slug: 'cleaning-household', label: 'Cleaning & Household' },
    { slug: 'health-beauty',      label: 'Health & Beauty' },
    { slug: 'pet-supplies',       label: 'Pet Supplies' },
    { slug: 'alcohol',            label: 'Alcohol' },
];
