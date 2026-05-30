from backend.app.agents.playbook_selector import detect_attack_type, select_playbook, TEMPLATES


class TestDetectAttackType:
    def test_brute_force(self):
        alert = {"description": "SSH bruteforce detected", "tags": []}
        assert detect_attack_type(alert) == "brute_force"

    def test_port_scan(self):
        alert = {"description": "Port scan on multiple ports", "tags": ["nmap"]}
        assert detect_attack_type(alert) == "port_scan"

    def test_exfiltration(self):
        alert = {"description": "DNS tunnel exfiltration", "tags": []}
        assert detect_attack_type(alert) == "data_exfiltration"

    def test_phishing(self):
        alert = {"description": "Phishing email detected", "tags": []}
        assert detect_attack_type(alert) == "phishing"

    def test_ddos(self):
        alert = {"description": "DDoS flood attack", "tags": []}
        assert detect_attack_type(alert) == "ddos"

    def test_unknown(self):
        alert = {"description": "Something happened", "tags": []}
        assert detect_attack_type(alert) == "unknown"

    def test_keywords_in_tags(self):
        alert = {"description": "alert", "tags": ["bruteforce", "ssh"]}
        assert detect_attack_type(alert) == "brute_force"


class TestSelectPlaybook:
    def test_brute_force_template(self):
        alert = {"description": "SSH bruteforce", "tags": []}
        pb = select_playbook(alert)
        assert pb["template_name"] == "brute_force"
        assert pb.get("skip_recon") is True
        assert pb["risk_block_threshold"] == 60

    def test_ddos_template(self):
        alert = {"description": "DDoS flood", "tags": []}
        pb = select_playbook(alert)
        assert pb["template_name"] == "ddos"
        assert pb["risk_block_threshold"] == 40

    def test_phishing_no_firewall(self):
        alert = {"description": "Phishing email", "tags": []}
        pb = select_playbook(alert)
        assert "firewall_block" not in pb["steps"]

    def test_unknown_with_benign_intel(self):
        alert = {"description": "Something unknown", "tags": []}
        intel = {"reputation": "benign"}
        pb = select_playbook(alert, intel=intel)
        assert pb["template_name"] == "low_priority"

    def test_unknown_without_intel(self):
        alert = {"description": "Something unknown", "tags": []}
        pb = select_playbook(alert)
        assert pb["template_name"] == "full_investigation"

    def test_all_templates_valid(self):
        for name, template in TEMPLATES.items():
            assert "steps" in template
            assert "risk_block_threshold" in template
            assert isinstance(template["steps"], list)

    def test_result_has_detected_type(self):
        alert = {"description": "Port scan", "tags": []}
        pb = select_playbook(alert)
        assert "detected_attack_type" in pb
        assert pb["detected_attack_type"] == "port_scan"
