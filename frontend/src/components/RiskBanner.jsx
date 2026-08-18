import { ShieldAlert, ShieldCheck, Shield, ShieldX } from "lucide-react";

const CONFIG = {
  "Low Risk": { cls: "risk-low", Icon: ShieldCheck },
  "Medium Risk": { cls: "risk-med", Icon: Shield },
  "High Risk": { cls: "risk-high", Icon: ShieldAlert },
  "Very High Risk": { cls: "risk-vh", Icon: ShieldX },
};

export default function RiskBanner({ risk }) {
  const { cls, Icon } = CONFIG[risk] || CONFIG["Medium Risk"];
  return (
    <div className={`risk-banner ${cls} scale-in`}>
      <Icon size={22} />
      <span>Overall Risk: <strong>{risk}</strong></span>
    </div>
  );
}
