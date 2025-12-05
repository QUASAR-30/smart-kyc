// TypeScript types and interfaces

export interface ITrustScore {
  trustscore: number;
  badge: BadgeLevel;
  metrics: IMetrics;
  calculation_mode: 'COLD_START' | 'NORMAL';
  valid_until: string;
}

export type BadgeLevel = 'NONE' | 'BRONZE' | 'SILVER' | 'GOLD' | 'PLATINUM';

export interface IMetrics {
  documents: number;
  historique: number;
  comportement: number;
  financiers: number;
}

export interface IMerchant {
  id: string;
  email: string;
  business_name: string;
  subscription_tier: 'FREE' | 'BASIC' | 'PRO' | 'ENTERPRISE';
}
