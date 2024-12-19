
import copy

from config.bn_config import parent_node_dict, field_device_belonging
from pgmpy.models import BayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination


class AttackRisAssessment:

    def __init__(self):
        
        self.parent_dict = parent_node_dict
        self.cyber_device = ['DBS','HIS','EWS','PLC1','PLC2']
        self.field_device = field_device_belonging['PLC1'] + field_device_belonging['PLC2']

        self.cp_device = self.cyber_device + self.field_device

        self.model = self.create_BN_model()
        self.initialize_cpds()
        print(self.model.check_model())


    def get_ad_evidence(self, ad_result):
        
        ad_evidence = {}
        ad_result_set = set(ad_result)
        cyber_device_set = set(self.cyber_device)
        cp_device_set = set(self.cp_device)

        # Attack evidence
        ad_evidence = {alarm: 1 for alarm in ad_result_set & cp_device_set}

        # Not attacked evidence
        not_attacked = cyber_device_set - ad_result_set

        ad_evidence.update({device: 0 for device in not_attacked if device not in ['PLC1', 'PLC2']})

        return ad_evidence


    def create_BN_model(self):
        edges = []
        for node, data in self.parent_dict.items():
            for parent in data['parents']:
                edges.append((parent, node))

        model = BayesianNetwork(edges)
        return model


    def initialize_cpds(self):

        for node, info in self.parent_dict.items():
            parents = info['parents']
            cpd_values = info['cpd']
            cpd = TabularCPD(
                    variable=node, variable_card=2, 
                    values=cpd_values,
                    evidence=parents,
                    evidence_card=[2]*len(parents))            
            self.model.add_cpds(cpd)


    def perform_inference(self, evidence, criticality_score = None):

        inference = VariableElimination(self.model)
        attack_prob_list = []
        attack_prob_list = {}
        field_device = copy.deepcopy(self.field_device)

        alarm_device = list(evidence.keys())
        for device in alarm_device:
            if device in self.field_device:
                attack_prob_list[device] = 1
                del evidence[device]
                field_device.remove(device)

        for i, node in enumerate(field_device):

            query_result = inference.query([node], evidence=evidence)
            for state, prob in zip(query_result.state_names[node], query_result.values):
                if state == 1:
                    attack_prob_list[node] = round(prob,3)

        attack_prob = 0
        if criticality_score is None:
            attack_prob = sum(list(attack_prob_list.values()))/ len(self.field_device)
        else:
            for key, value in attack_prob_list.items():
                attack_prob += criticality_score[key] * value
            attack_prob /= len(self.field_device)

        return attack_prob


