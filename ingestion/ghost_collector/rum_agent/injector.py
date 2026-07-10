"""
OmniWatch 2.0 — GhostCollector
Component: RUM Injector
Layer: 2
Phase: 5
Purpose: Auto-injects JavaScript RUM snippet into HTML responses
Inputs: HTTP responses with Content-Type: text/html
Outputs: RUM data to Kafka omniwatch.telemetry.raw
Technology: Python, beautifulsoup4
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

RUM_SNIPPET = """
<script data-omniwatch-rum="true">
(function() {
  var ow = window.OmniWatchRUM = { q: [] };
  ow.track = function(name, data) { ow.q.push({name:name, data:data, ts:Date.now()}); };

  // Core Web Vitals
  if (typeof PerformanceObserver !== 'undefined') {
    new PerformanceObserver(function(list) {
      list.getEntries().forEach(function(e) {
        if (e.name === 'largest-contentful-paint') ow.track('LCP', {value:e.startTime});
        if (e.name === 'first-input') ow.track('FID', {value:e.processingStart - e.startTime});
      });
    }).observe({type:'largest-contentful-paint', buffered:true});
    new PerformanceObserver(function(list) {
      list.getEntries().forEach(function(e) {
        if (e.hadRecentInput) return;
        ow.track('CLS', {value:e.value});
      });
    }).observe({type:'layout-shift', buffered:true});
  }

  // Error tracking
  window.addEventListener('error', function(e) {
    ow.track('error', {message:e.message, source:e.filename, line:e.lineno});
  });

  // Send buffered events every 10s
  setInterval(function() {
    if (ow.q.length === 0) return;
    var events = ow.q.splice(0);
    navigator.sendBeacon('/__omniwatch_rum', JSON.stringify(events));
  }, 10000);
})();
</script>
"""


class RUMInjector:
    """Injects RUM JavaScript snippet into HTML responses."""

    def __init__(self):
        self._inject_count = 0

    def inject(self, html_content: str) -> str:
        """Inject RUM snippet into HTML content.

        Args:
            html_content: Original HTML response.

        Returns:
            HTML with RUM snippet injected before </head>.
        """
        if "</head>" in html_content:
            html_content = html_content.replace("</head>", RUM_SNIPPET + "\n</head>", 1)
            self._inject_count += 1
        elif "<body>" in html_content:
            html_content = html_content.replace("<body>", RUM_SNIPPET + "\n<body>", 1)
            self._inject_count += 1

        return html_content

    def should_inject(self, headers: dict[str, str]) -> bool:
        """Check if RUM should be injected based on response headers.

        Args:
            headers: Response headers dict.

        Returns:
            True if content is HTML and should be instrumented.
        """
        content_type = headers.get("content-type", headers.get("Content-Type", ""))
        return "text/html" in content_type

    def get_stats(self) -> dict[str, Any]:
        return {"inject_count": self._inject_count}
