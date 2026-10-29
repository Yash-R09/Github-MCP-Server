variable "alert_email" {
  type        = string
  description = "Email address for CloudWatch alarm notifications"
}

resource "aws_cloudwatch_log_metric_filter" "tool_call_errors" {
  name           = "${var.project}-tool-call-errors"
  log_group_name = aws_cloudwatch_log_group.app.name

  pattern = "{ $.event = \"tool_call\" && $.status = \"error\" }"

  metric_transformation {
    name      = "ToolCallErrors"
    namespace = "GitHubMCP"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "tool_call_latency" {
  name           = "${var.project}-tool-call-latency"
  log_group_name = aws_cloudwatch_log_group.app.name

  pattern = "{ $.event = \"tool_call\" }"

  metric_transformation {
    name          = "ToolCallLatency"
    namespace     = "GitHubMCP"
    value         = "$.duration_ms"
    default_value = 0
  }
}

resource "aws_sns_topic" "alerts" {
  name = "${var.project}-alerts"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

resource "aws_cloudwatch_metric_alarm" "tool_call_errors" {
  alarm_name          = "${var.project}-tool-call-errors"
  alarm_description   = "Three or more failed MCP tool calls in five minutes"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  threshold           = 3
  period              = 300
  statistic           = "Sum"
  namespace           = "GitHubMCP"
  metric_name         = "ToolCallErrors"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "tool_call_latency" {
  alarm_name          = "${var.project}-tool-call-latency"
  alarm_description   = "Average MCP tool call latency exceeds five seconds"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = 5000
  period              = 300
  statistic           = "Average"
  namespace           = "GitHubMCP"
  metric_name         = "ToolCallLatency"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = var.project

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "MCP Tool Call Errors"
          view    = "timeSeries"
          region  = var.aws_region
          period  = 300
          stat    = "Sum"
          metrics = [["GitHubMCP", "ToolCallErrors"]]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "MCP Tool Call Latency"
          view   = "timeSeries"
          region = var.aws_region
          period = 300
          metrics = [
            ["GitHubMCP", "ToolCallLatency", { stat = "Average", label = "Average" }],
            ["...", { stat = "p50", label = "p50" }],
            ["...", { stat = "p95", label = "p95" }]
          ]
        }
      }
    ]
  })
}