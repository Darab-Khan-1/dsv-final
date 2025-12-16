import { 
  ResponsiveContainer, 
  AreaChart as RechartsAreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip 
} from 'recharts';

interface AreaChartProps {
  data: Record<string, any>[];
  xKey: string;
  yKey: string;
  height?: number;
  color?: string;
}

export function AreaChart({ 
  data, 
  xKey, 
  yKey,
  height = 300,
  color = 'hsl(187, 85%, 53%)'
}: AreaChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsAreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.3} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(222, 30%, 18%)" />
        <XAxis 
          dataKey={xKey} 
          stroke="hsl(215, 20%, 55%)" 
          fontSize={12}
          tickLine={false}
          axisLine={{ stroke: 'hsl(222, 30%, 18%)' }}
        />
        <YAxis 
          stroke="hsl(215, 20%, 55%)" 
          fontSize={12}
          tickLine={false}
          axisLine={{ stroke: 'hsl(222, 30%, 18%)' }}
        />
        <Tooltip 
          contentStyle={{ 
            backgroundColor: 'hsl(222, 47%, 8%)', 
            border: '1px solid hsl(222, 30%, 18%)',
            borderRadius: '8px',
            color: 'hsl(210, 40%, 98%)'
          }}
        />
        <Area 
          type="monotone" 
          dataKey={yKey} 
          stroke={color}
          strokeWidth={2}
          fill="url(#areaGradient)"
        />
      </RechartsAreaChart>
    </ResponsiveContainer>
  );
}
