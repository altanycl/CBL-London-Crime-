export let dutySheetCache: { value: any[] | null } = { value: null };
export function setDutySheetCache(data: any[]) {
  dutySheetCache.value = data;
} 