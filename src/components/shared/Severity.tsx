type SeverityProps = {
  level: string;
};

export default function Severity({ level }: SeverityProps) {
  return (
    <span className={`severity severity--${level.toLowerCase()}`}>
      <i />
      {level}
    </span>
  );
}