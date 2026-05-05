export interface Column<T> {
    key: keyof T & string;
    label: string;
    /** Shown in mobile card layout. Defaults to `label`. */
    mobileLabel?: string;
    sortable?: boolean;
    align?: 'left' | 'center' | 'right';
    /** Custom cell renderer snippet */
    cell?: import('svelte').Snippet<[T]>;
}
