import React from 'react';
import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from 'recharts';

interface TrustScoreGaugeProps {
    score: number;
    badge: string;
}

const TrustScoreGauge: React.FC<TrustScoreGaugeProps> = ({ score, badge }) => {
    // Determine color based on score
    const getColor = (score: number) => {
        if (score >= 850) return '#10B981'; // Emerald-500 (Platinum)
        if (score >= 700) return '#FBBF24'; // Amber-400 (Gold)
        if (score >= 550) return '#9CA3AF'; // Gray-400 (Silver)
        if (score >= 400) return '#B45309'; // Amber-700 (Bronze)
        return '#EF4444'; // Red-500 (None)
    };

    const color = getColor(score);

    const data = [
        {
            name: 'TrustScore',
            value: score,
            fill: color,
        },
    ];

    return (
        <div className="relative flex flex-col items-center justify-center">
            <div className="h-64 w-64">
                <ResponsiveContainer width="100%" height="100%">
                    <RadialBarChart
                        cx="50%"
                        cy="50%"
                        innerRadius="80%"
                        outerRadius="100%"
                        barSize={20}
                        data={data}
                        startAngle={180}
                        endAngle={0}
                    >
                        <PolarAngleAxis
                            type="number"
                            domain={[0, 1000]}
                            angleAxisId={0}
                            tick={false}
                        />
                        <RadialBar
                            background
                            dataKey="value"
                            cornerRadius={10}
                            fill={color}
                        />
                    </RadialBarChart>
                </ResponsiveContainer>
            </div>

            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/4 text-center mt-4">
                <div className="text-4xl font-bold text-slate-900">{score}</div>
                <div className="text-sm text-slate-500 uppercase tracking-wider mt-1">TrustScore</div>
                <div
                    className="mt-2 px-3 py-1 rounded-full text-xs font-bold text-white uppercase"
                    style={{ backgroundColor: color }}
                >
                    {badge} Badge
                </div>
            </div>
        </div>
    );
};

export default TrustScoreGauge;
