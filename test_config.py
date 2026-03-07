import unittest, copy
from typing import Any
from main import validateYaml

class TestValidateYaml(unittest.TestCase):

    def setUp(self) -> None:
        # Base valid YAML for reuse
        self.valid_yaml: dict[str, Any] = {
            "defaults": {
                "snmp_version": "v2c",
                "timeout_s": 2.5,
                "retries": 1,
                "target_budget_s": 10,
                "oids": ["sysUpTime.0", "sysName.0"]
            },
            "targets": [
                {
                    "name": "router1",
                    "ip": "10.0.0.1",
                    "community": "public",
                    "oids": ["ifOperStatus.1"]
                },
                {
                    "name": "router2",
                    "ip": "10.0.0.2",
                    "community": "public"
                }
            ]
        }

    def test_valid_yaml(self):
        """Valid YAML passes validation"""
        result, msg = validateYaml(self.valid_yaml)
        self.assertTrue(result, msg)

    def test_non_numeric_timeout(self):
        """Non-numeric timeout_s is rejected"""
        yaml_copy = copy.deepcopy(self.valid_yaml)
        yaml_copy["defaults"]["timeout_s"] = "two"
        result, msg = validateYaml(yaml_copy)
        self.assertFalse(result)
        self.assertIn("timeout_s", msg)

    def test_missing_targets(self):
        """Missing 'targets' key fails validation"""
        yaml_copy = dict(self.valid_yaml)
        yaml_copy.pop("targets")
        result, msg = validateYaml(yaml_copy)
        self.assertFalse(result)
        self.assertIn("targets", msg)

    def test_target_missing_ip(self):
        """Target missing 'ip' is rejected"""
        yaml_copy = copy.deepcopy(self.valid_yaml)
        yaml_copy["targets"][0].pop("ip")
        result, msg = validateYaml(yaml_copy)
        self.assertFalse(result)
        self.assertIn("ip", msg)

    def test_invalid_ip_in_targets(self):
        """Targets with invalid IP addresses are rejected"""
        yaml_copy = copy.deepcopy(self.valid_yaml)
        yaml_copy["targets"][0]["ip"] = "999.999.999.999"  # invalid IPv4
        result, msg = validateYaml(yaml_copy)
        self.assertFalse(result)
        self.assertIn("invalid IP address", msg)


if __name__ == "__main__":
    unittest.main()