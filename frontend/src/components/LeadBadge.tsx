/**
 * BizMind AI — LeadBadge Component
 * Colored status badge for hot/warm/cold leads.
 */

interface LeadBadgeProps {
  status: "hot" | "warm" | "cold";
  size?: "sm" | "md";
}

const badgeConfig = {
  hot: {
    label: "Hot",
    className: "bg-error/15 text-error border border-error/30",
    dot: "bg-error",
    icon: "local_fire_department",
  },
  warm: {
    label: "Warm",
    className: "bg-tertiary/15 text-tertiary border border-tertiary/30",
    dot: "bg-tertiary",
    icon: "trending_up",
  },
  cold: {
    label: "Cold",
    className: "bg-primary/15 text-primary border border-primary/30",
    dot: "bg-primary",
    icon: "ac_unit",
  },
};

export default function LeadBadge({ status, size = "md" }: LeadBadgeProps) {
  const config = badgeConfig[status] || badgeConfig.cold;
  const sizeClass = size === "sm" ? "text-xs px-2 py-0.5 gap-1" : "text-xs px-2.5 py-1 gap-1.5";

  return (
    <span
      className={`inline-flex items-center rounded-full font-medium ${config.className} ${sizeClass}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot} shrink-0`} />
      {config.label}
    </span>
  );
}
