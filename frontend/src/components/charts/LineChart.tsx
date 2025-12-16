import { 
  ResponsiveContainer, 
  LineChart as RechartsLineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip,
  Legend 
} from 'recharts';

interface LineChartProps {
  data: Record<string, any>[];
  xKey: string;
  yKey: string | string[];
  xLabel?: string;
  yLabel?: string;
  height?: number;
  colors?: string[];
}

export function LineChart({ 
  data, 
  xKey, 
  yKey, 
  xLabel,
  yLabel,
  height = 300,
  colors = ['hsl(187, 85%, 53%)', 'hsl(280, 65%, 60%)', 'hsl(45, 93%, 58%)']
}: LineChartProps) {
  const yKeys = Array.isArray(yKey) ? yKey : [yKey];

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsLineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(222, 30%, 18%)" />
        <XAxis 
          dataKey={xKey} 
          stroke="hsl(215, 20%, 55%)" 
          fontSize={12}
          tickLine={false}
          axisLine={{ stroke: 'hsl(222, 30%, 18%)' }}
          label={xLabel ? { value: xLabel, position: 'bottom', fill: 'hsl(215, 20%, 55%)' } : undefined}
        />
        <YAxis 
          stroke="hsl(215, 20%, 55%)" 
          fontSize={12}
          tickLine={false}
          axisLine={{ stroke: 'hsl(222, 30%, 18%)' }}
          label={yLabel ? { value: yLabel, angle: -90, position: 'insideLeft', fill: 'hsl(215, 20%, 55%)' } : undefined}
        />
        <Tooltip 
          contentStyle={{ 
            backgroundColor: 'hsl(222, 47%, 8%)', 
            border: '1px solid hsl(222, 30%, 18%)',
            borderRadius: '8px',
            color: 'hsl(210, 40%, 98%)'
          }}
        />
        {yKeys.length > 1 && <Legend />}
        {yKeys.map((key, index) => (
          <Line 
            key={key}
            type="monotone" 
            dataKey={key} 
            stroke={colors[index % colors.length]}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 6, fill: colors[index % colors.length] }}
          />
        ))}
      </RechartsLineChart>
    </ResponsiveContainer>
  );
}
