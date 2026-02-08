import { DocumentService } from '../services/documentService';
import { JournalService } from '../services/journalService';
import { SettingService } from '../services/settingService';
import { InventoryService } from '../services/inventoryService';
import { ProductionService } from '../services/productionService';
import { GncService } from '../services/gncService';

const API_URL = import.meta.env.VITE_API_URL || '';

export const docService = new DocumentService(API_URL);
export const journalService = new JournalService(API_URL);
export const settingService = new SettingService(API_URL);
export const inventoryService = new InventoryService(API_URL);
export const productionService = new ProductionService(API_URL);
export const gncService = new GncService(API_URL);

// State using Svelte 5 Runes (standardized approach)
// This file can be imported into components
