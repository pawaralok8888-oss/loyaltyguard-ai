import React from 'react';

/**
 * Clean inline SVG illustration for the Dashboard Hero Banner.
 * Depicts a calm fintech points wallet with a small expiry clock badge and reward star tokens.
 */
export const HeroWalletIllustration: React.FC<{ className?: string }> = ({ className = "w-40 h-32" }) => (
  <svg
    viewBox="0 0 240 180"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    aria-label="Points wallet with expiry protection"
  >
    <defs>
      <linearGradient id="walletGrad" x1="20" y1="30" x2="190" y2="160" gradientUnits="userSpaceOnUse">
        <stop stopColor="#4F46E5" />
        <stop offset="1" stopColor="#3730A3" />
      </linearGradient>
      <linearGradient id="cardGrad" x1="50" y1="20" x2="170" y2="90" gradientUnits="userSpaceOnUse">
        <stop stopColor="#6366F1" />
        <stop offset="1" stopColor="#4338CA" />
      </linearGradient>
      <linearGradient id="goldGrad" x1="0" y1="0" x2="1" y2="1">
        <stop stopColor="#F59E0B" />
        <stop offset="1" stopColor="#D97706" />
      </linearGradient>
      <filter id="shadow" x="10" y="25" width="200" height="150" filterUnits="userSpaceOnUse">
        <feDropShadow dx="0" dy="8" stdDeviation="10" floodColor="#1E1B4B" floodOpacity="0.2" />
      </filter>
    </defs>

    {/* Back card sticking out */}
    <rect x="55" y="22" width="120" height="70" rx="8" fill="url(#cardGrad)" opacity="0.85" />
    <rect x="65" y="32" width="40" height="8" rx="2" fill="#C7D2FE" opacity="0.6" />
    <circle cx="155" cy="40" r="10" fill="#FCD34D" opacity="0.7" />

    {/* Main Wallet Body */}
    <g filter="url(#shadow)">
      <rect x="30" y="45" width="160" height="105" rx="14" fill="url(#walletGrad)" />
      {/* Wallet Stitching Accent */}
      <rect x="35" y="50" width="150" height="95" rx="10" stroke="#818CF8" strokeWidth="1" strokeDasharray="3 3" fill="none" opacity="0.6" />
      {/* Flap */}
      <path d="M30 55 C 30 55, 110 85, 190 55 L 190 68 C 110 98, 30 68, 30 68 Z" fill="#312E81" opacity="0.4" />
      {/* Clasp */}
      <rect x="160" y="82" width="30" height="24" rx="6" fill="#1E1B4B" />
      <circle cx="170" cy="94" r="4" fill="url(#goldGrad)" />
    </g>

    {/* Reward Coin floating */}
    <g transform="translate(25, 20)">
      <circle cx="16" cy="16" r="16" fill="url(#goldGrad)" />
      <circle cx="16" cy="16" r="13" stroke="#FDE68A" strokeWidth="1.5" fill="none" />
      <path d="M16 8 L18.5 13.5 L24 14.2 L19.8 18 L21 23.5 L16 20.6 L11 23.5 L12.2 18 L8 14.2 L13.5 13.5 Z" fill="#FFFBEB" />
    </g>

    {/* Expiry Clock Badge floating bottom right */}
    <g transform="translate(150, 100)">
      <circle cx="28" cy="28" r="24" fill="#FFFFFF" />
      <circle cx="28" cy="28" r="22" fill="#FEF3C7" stroke="#F59E0B" strokeWidth="2.5" />
      {/* Clock ticks */}
      <circle cx="28" cy="28" r="2.5" fill="#B45309" />
      <path d="M28 15 V28 L36 32" stroke="#B45309" strokeWidth="2.5" strokeLinecap="round" />
      {/* Subtle pulse ring */}
      <circle cx="28" cy="28" r="26" stroke="#F59E0B" strokeWidth="1" strokeDasharray="2 2" fill="none" opacity="0.6" />
    </g>
  </svg>
);

/**
 * Empty state: No Accounts illustration
 */
export const EmptyAccountsIllustration: React.FC<{ className?: string }> = ({ className = "w-24 h-24" }) => (
  <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
    <rect x="18" y="24" width="64" height="48" rx="8" fill="#EEF2FF" stroke="#C7D2FE" strokeWidth="2" strokeDasharray="4 4" />
    <rect x="28" y="34" width="24" height="6" rx="3" fill="#A5B4FC" />
    <circle cx="66" cy="48" r="10" fill="#E0E7FF" />
    <path d="M66 43 V53 M61 48 H71" stroke="#4F46E5" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

/**
 * Empty state: No Batches / Calendar illustration
 */
export const EmptyBatchesIllustration: React.FC<{ className?: string }> = ({ className = "w-24 h-24" }) => (
  <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
    <rect x="20" y="22" width="60" height="56" rx="8" fill="#F8FAFC" stroke="#E2E8F0" strokeWidth="2" />
    <path d="M20 36 H80" stroke="#E2E8F0" strokeWidth="2" />
    <rect x="30" y="16" width="6" height="10" rx="2" fill="#4F46E5" />
    <rect x="64" y="16" width="6" height="10" rx="2" fill="#4F46E5" />
    <circle cx="50" cy="54" r="12" fill="#CCFBF1" />
    <path d="M44 54 L48 58 L57 49" stroke="#0D9488" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

/**
 * Empty state: No Alerts illustration
 */
export const EmptyAlertsIllustration: React.FC<{ className?: string }> = ({ className = "w-24 h-24" }) => (
  <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
    <path
      d="M50 20 C42 20 36 26 36 34 C36 48 30 54 30 54 H70 C70 54 64 48 64 34 C64 26 58 20 50 20 Z"
      fill="#F8FAFC"
      stroke="#CBD5E1"
      strokeWidth="2"
    />
    <path d="M46 58 C46 60.5 47.8 62.5 50 62.5 C52.2 62.5 54 60.5 54 58" stroke="#94A3B8" strokeWidth="2" strokeLinecap="round" />
    <circle cx="66" cy="26" r="8" fill="#CCFBF1" stroke="#FFFFFF" strokeWidth="2" />
    <path d="M63 26 L65 28 L69 24" stroke="#0D9488" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

/**
 * Empty state: No Agent Runs illustration
 */
export const EmptyAgentRunsIllustration: React.FC<{ className?: string }> = ({ className = "w-24 h-24" }) => (
  <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
    <rect x="22" y="26" width="56" height="48" rx="8" fill="#F8FAFC" stroke="#E2E8F0" strokeWidth="2" />
    <rect x="30" y="34" width="40" height="20" rx="4" fill="#0F172A" />
    <path d="M36 41 L40 44 L36 47" stroke="#4ADE80" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    <line x1="43" y1="47" x2="48" y2="47" stroke="#4ADE80" strokeWidth="1.5" strokeLinecap="round" />
    <circle cx="36" cy="62" r="3" fill="#6366F1" />
    <circle cx="50" cy="62" r="3" fill="#A5B4FC" />
    <circle cx="64" cy="62" r="3" fill="#E0E7FF" />
  </svg>
);

/**
 * Program Badge: A coloured circle with the program's initials instead of a logo.
 */
export const ProgramBadge: React.FC<{
  providerCode?: string;
  displayName?: string;
  size?: 'sm' | 'md' | 'lg';
}> = ({ providerCode = '', displayName = '', size = 'md' }) => {
  // Determine initials
  let initials = '';
  if (providerCode === 'shop_rewards') {
    initials = 'SR';
  } else if (providerCode === 'fly_miles') {
    initials = 'FM';
  } else if (providerCode === 'gift_hub') {
    initials = 'GH';
  } else if (displayName.includes('TC3')) {
    initials = 'T3';
  } else if (displayName.includes('TC4')) {
    initials = 'T4';
  } else if (displayName.includes('TC1')) {
    initials = 'T1';
  } else if (displayName) {
    const parts = displayName.trim().split(/\s+/);
    initials = parts.length >= 2 ? (parts[0][0] + parts[1][0]).toUpperCase() : displayName.slice(0, 2).toUpperCase();
  } else {
    initials = providerCode.slice(0, 2).toUpperCase() || 'LP';
  }

  // Calm fintech palette for programs
  let colorClasses = 'bg-indigo-50 text-indigo-700 border-indigo-200';
  if (providerCode === 'fly_miles') {
    colorClasses = 'bg-sky-50 text-sky-700 border-sky-200';
  } else if (providerCode === 'gift_hub') {
    colorClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  } else if (initials === 'T3') {
    colorClasses = 'bg-rose-50 text-rose-700 border-rose-200';
  } else if (initials === 'T4') {
    colorClasses = 'bg-amber-50 text-amber-700 border-amber-200';
  }

  const sizeClasses =
    size === 'sm'
      ? 'w-7 h-7 text-[11px]'
      : size === 'lg'
      ? 'w-11 h-11 text-sm'
      : 'w-9 h-9 text-xs';

  return (
    <div
      className={`${sizeClasses} ${colorClasses} rounded-full flex items-center justify-center font-bold border flex-shrink-0 shadow-xs tracking-wider`}
      title={displayName || providerCode}
      aria-label={initials}
    >
      {initials}
    </div>
  );
};
