/**
 * BizMind AI — StatsCard Component
 * Reusable metric card for the dashboard.
 */
interface StatsCardProps {
  title: string;
  value: string | number;
  icon: string;
  subtitle?: string;
  trend?: { value: number; label: string };
  accent?: "primary" | "secondary" | "tertiary" | "error";
}

const accentMap = {
  primary: {
    icon: "bg-primary-container/20 text-primary",
    border: "border-primary/20",
  },
  secondary: {
    icon: "bg-secondary-container/20 text-secondary",
    border: "border-secondary/20",
  },
  tertiary: {
    icon: "bg-tertiary-container/20 text-tertiary",
    border: "border-tertiary/20",
  },
  error: {
    icon: "bg-error-container/20 text-error",
    border: "border-error/20",
  },
};

export default function StatsCard({
  title,
  value,
  icon,
  subtitle,
  trend,
  accent = "primary",
}: StatsCardProps) {
  const colors = accentMap[accent];
  const isPositive = trend ? trend.value >= 0 : null;

  return (
    <div
      className={`rounded-xl border ${colors.border} bg-surface-container p-5 flex flex-col gap-4 hover:bg-surface-container-high transition-colors`}
    >
      <div className="flex items-start justify-between">
        <div className={`p-2 rounded-lg ${colors.icon}`}>
          <span className="material-symbols-outlined text-xl">{icon}</span>
        </div>
        {trend && (
          <span
            className={`text-xs font-medium px-2 py-1 rounded-full ${
              isPositive
                ? "text-secondary bg-secondary-container/20"
                : "text-error bg-error-container/20"
            }`}
          >
            {isPositive ? "↑" : "↓"} {Math.abs(trend.value)}% {trend.label}
          </span>
        )}
      </div>
      <div>
        <p className="text-2xl font-bold text-on-surface">{value}</p>
        <p className="text-sm text-on-surface-variant mt-0.5">{title}</p>
        {subtitle && (
          <p className="text-xs text-on-surface-variant/60 mt-1">{subtitle}</p>
        )}
      </div>
    </div>
  );
}
