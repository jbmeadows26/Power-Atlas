import {createContext,useContext} from 'react';
// Presentation filters only. Never rewrite or infer a source record's date or grade.
export type Horizon='all'|'24h'|'7d'|'30d';
export type Severity='all'|'elevated'|'review'|'monitor';
export const GlobalFiltersContext=createContext<{horizon:Horizon;severity:Severity}>({horizon:'all',severity:'all'});
export const useGlobalFilters=()=>useContext(GlobalFiltersContext);
