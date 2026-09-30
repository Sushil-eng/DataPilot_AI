import React from 'react';
import { Card, CardHeader, CardContent } from '@/components/Card';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { cn } from '@/utils/cn';

interface ChartCardProps {
  title: string;
  description?: string;
  data: any[];
  dataKey: string;
  xAxisKey: string;
  className?: string;
}

export const ChartCard: React.FC<ChartCardProps> = ({
  title,
  description,
  data,
  dataKey,
  xAxisKey,
  className,
}) => {
  return (
    <Card variant="bordered" padding="md" className={cn("flex flex-col min-w-0 overflow-hidden", className)}>
      <CardHeader 
        title={title} 
        description={description} 
        className="mb-6"
      />
      <CardContent className="h-[300px] w-full min-w-0 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--color-dp-accent)" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="var(--color-dp-accent)" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-dp-border)" vertical={false} />
            <XAxis 
              dataKey={xAxisKey} 
              stroke="var(--color-dp-text-muted)" 
              fontSize={12}
              tickLine={false}
              axisLine={false}
              dy={10}
            />
            <YAxis 
              stroke="var(--color-dp-text-muted)" 
              fontSize={12}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${value}`}
            />
            <Tooltip
              contentStyle={{ 
                backgroundColor: 'var(--color-dp-bg-raised)',
                border: '1px solid var(--color-dp-border)',
                borderRadius: 'var(--radius-card)',
                color: 'var(--color-dp-text)'
              }}
              itemStyle={{ color: 'var(--color-dp-accent)' }}
            />
            <Area 
              type="monotone" 
              dataKey={dataKey} 
              stroke="var(--color-dp-accent)" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorValue)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};
