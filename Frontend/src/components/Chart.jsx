import React from 'react'
import Plot from 'react-plotly.js'

export function Chart({ config }) {
  if (!config || !config.data) {
    return null
  }

  return (
    <div className="my-4 bg-white dark:bg-slate-900 p-4 rounded-lg border border-slate-200 dark:border-slate-700">
      <Plot
        data={config.data}
        layout={{
          ...config.layout,
          autosize: true,
          paper_bgcolor: 'rgba(0,0,0,0)',
          plot_bgcolor: 'rgba(0,0,0,0)',
          font: {
            family: 'system-ui, -apple-system, sans-serif',
            size: 12
          }
        }}
        config={{
          responsive: true,
          displayModeBar: true,
          displaylogo: false,
          modeBarButtonsToRemove: ['lasso2d', 'select2d']
        }}
        style={{ width: '100%', height: '400px' }}
        useResizeHandler={true}
      />
    </div>
  )
}
