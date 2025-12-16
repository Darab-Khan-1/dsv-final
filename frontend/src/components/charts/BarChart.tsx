import { 
  ResponsiveContainer, 
  BarChart as RechartsBarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip,
  Cell
} from 'recharts';

interface BarChartProps {
  data: Record<string, any>[];
  xKey: string;
  yKey: string;
  height?: number;
  color?: string;
  gradient?: boolean;
}

export function BarChart({ 
  data, 
  xKey, 
  yKey,
  height = 300,
  color = 'hsl(187, 85%, 53%)',
  gradient = true
}: BarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsBarChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={1} />
            <stop offset="100%" stopColor={color} stopOpacity={0.6} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(222, 30%, 18%)" vertical={false} />
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
          cursor={{ fill: 'hsl(222, 30%, 15%)' }}
        />
        <Bar 
          dataKey={yKey} 
          fill={gradient ? 'url(#barGradient)' : color}
          radius={[4, 4, 0, 0]}
        />
      </RechartsBarChart>
    </ResponsiveContainer>
  );
}

interface HorizontalBarChartProps {
  data: Record<string, any>[];
  nameKey: string;
  valueKey: string;
  height?: number;
  colors?: string[];
}

export function HorizontalBarChart({ 
  data, 
  nameKey, 
  valueKey,
  height = 300,
  colors = ['hsl(187, 85%, 53%)', 'hsl(200, 80%, 50%)', 'hsl(187, 85%, 43%)']
}: HorizontalBarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsBarChart data={data} layout="vertical" margin={{ top: 10, right: 30, left: 60, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(222, 30%, 18%)" horizontal={false} />
        <XAxis 
          type="number"
          stroke="hsl(215, 20%, 55%)" 
          fontSize={12}
          tickLine={false}
          axisLine={{ stroke: 'hsl(222, 30%, 18%)' }}
        />
        <YAxis 
          type="category"
          dataKey={nameKey}
          stroke="hsl(215, 20%, 55%)" 
          fontSize={12}
          tickLine={false}
          axisLine={{ stroke: 'hsl(222, 30%, 18%)' }}
          width={50}
        />
        <Tooltip 
          contentStyle={{ 
            backgroundColor: 'hsl(222, 47%, 8%)', 
            border: '1px solid hsl(222, 30%, 18%)',
            borderRadius: '8px',
            color: 'hsl(210, 40%, 98%)'
          }}
          cursor={{ fill: 'hsl(222, 30%, 15%)' }}
        />
        <Bar dataKey={valueKey} radius={[0, 4, 4, 0]}>
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
          ))}
        </Bar>
      </RechartsBarChart>
    </ResponsiveContainer>
  );
}
