export const EXPENSE_CATEGORIES = [
  { value: 'food', label: 'Food' },
  { value: 'travel', label: 'Travel' },
  { value: 'shopping', label: 'Shopping' },
  { value: 'education', label: 'Education' },
  { value: 'entertainment', label: 'Entertainment' },
  { value: 'miscellaneous', label: 'Misc' },
];

export const INCOME_SOURCES = [
  { value: 'pocket_money', label: 'Pocket Money' },
  { value: 'scholarship', label: 'Scholarship' },
  { value: 'freelance', label: 'Freelance' },
];

export const EXPENSE_COLORS = {
  food: '#EF4444', travel: '#3B82F6', shopping: '#8B5CF6',
  education: '#10B981', entertainment: '#F59E0B', miscellaneous: '#6B7280',
};

export const INCOME_COLORS = {
  pocket_money: '#10B981', scholarship: '#3B82F6', freelance: '#8B5CF6',
};

export const MONTHS = [
  '', 'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

export const catLabel = (value) =>
  EXPENSE_CATEGORIES.find((c) => c.value === value)?.label || value;

export const currentMonth = () => new Date().getMonth() + 1;
export const currentYear = () => new Date().getFullYear();
