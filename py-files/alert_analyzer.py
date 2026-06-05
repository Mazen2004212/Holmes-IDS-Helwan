class AlertAnalyzer:
    def __init__(self, alerts):
        self.alerts = alerts

    def get_top_src_ip(self):
        src_ip_count = {}

        for alert in self.alerts:
            src_ip_count[alert.src_ip] = src_ip_count.get(alert.src_ip, 0) + 1

        top_ip = max(src_ip_count, key=src_ip_count.get, default="N/A")
        return top_ip

    def get_top_dst_ip(self):
        dst_ip_count = {}

        for alert in self.alerts:
            dst_ip_count[alert.dst_ip] = dst_ip_count.get(alert.dst_ip, 0) + 1

        top_ip = max(dst_ip_count, key=dst_ip_count.get, default="N/A")
        return top_ip

    def get_all_counts(self):
        return {
            "top_src_ip": self.get_top_src_ip(),
            "top_dst_ip": self.get_top_dst_ip(),
        }
