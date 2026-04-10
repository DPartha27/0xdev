"use client";

interface BadgeIndicatorProps {
    tier: string;
    size?: 'sm' | 'md' | 'lg';
}

const tierStyles: Record<string, string> = {
    'Bronze': 'bg-amber-700/20 text-amber-700 dark:bg-amber-700/30 dark:text-amber-400 border border-amber-700/30',
    'Silver': 'bg-gray-300/30 text-gray-600 dark:bg-gray-500/20 dark:text-gray-300 border border-gray-400/30',
    'Gold': 'bg-yellow-400/20 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-400 border border-yellow-500/30',
    'Platinum': 'bg-cyan-400/20 text-cyan-700 dark:bg-cyan-500/20 dark:text-cyan-300 border border-cyan-500/30',
    'Diamond': 'bg-blue-400/20 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300 border border-blue-500/30',
    'God': 'bg-gradient-to-r from-purple-500/20 via-pink-500/20 to-red-500/20 text-purple-700 dark:text-purple-300 border border-purple-500/30',
};

const sizeStyles: Record<string, string> = {
    sm: 'text-[10px] px-1.5 py-0.5',
    md: 'text-xs px-2 py-0.5',
    lg: 'text-sm px-3 py-1',
};

export default function BadgeIndicator({ tier, size = 'sm' }: BadgeIndicatorProps) {
    const tierBase = tier.split(' ')[0];
    const style = tierStyles[tierBase] || tierStyles['Bronze'];
    const sizeStyle = sizeStyles[size];

    return (
        <span className={`inline-flex items-center rounded-full font-medium whitespace-nowrap ${style} ${sizeStyle}`}>
            {tier}
        </span>
    );
}
