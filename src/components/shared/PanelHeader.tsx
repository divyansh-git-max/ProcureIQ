type PanelHeaderProps = {
  eyebrow: string;
  title: string;
  action?: string;
};

export default function PanelHeader({ eyebrow, title, action }: PanelHeaderProps) {
  return (
    <div className="panel-header">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h2>{title}</h2>
      </div>
      {action && <span className="panel-action">{action}</span>}
    </div>
  );
}