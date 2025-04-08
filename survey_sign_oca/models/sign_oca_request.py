# Copyright 2025 Kencove - Mohamed Alkobrosli
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class SurveyUtils:
    @staticmethod
    def is_yes_no_answer(value):
        return str(value).strip().lower() in ["yes", "no"]

    @staticmethod
    def answer_is_yes(value):
        return str(value).strip().lower() == "yes"

    @staticmethod
    def format_answer(answer):
        if SurveyUtils.is_yes_no_answer(answer):
            answer = SurveyUtils.answer_is_yes(answer)
        return answer


class SignOcaRequest(models.Model):
    _inherit = "sign.oca.request"

    # This field is required for the inverse of maintenance.equipment.
    survey_user_input_id = fields.Many2one(
        comodel_name="survey.user_input",
        compute="_compute_survey_user_input_id",
        string="Survey Participation",
        readonly=True,
        store=True,
        ondelete="cascade",
    )

    @api.depends("record_ref")
    def _compute_survey_user_input_id(self):
        for item in self.filtered(
            lambda x: x.record_ref and x.record_ref._name == "survey.user_input"
        ):
            item.survey_user_input_id = item.record_ref.id


class SignOcaRequestSigner(models.Model):

    _inherit = "sign.oca.request.signer"

    def get_related_survey_answers(self):
        self.ensure_one()
        # get survey answers for this sign request
        model_id = self.request_id.template_id.model_id
        survey_participation = self.request_id.record_ref
        survey = {}
        if survey_participation and model_id and model_id.model == "survey.user_input":
            for line in survey_participation.user_input_line_ids:
                if line.question_id.question_type == "matrix":
                    answer = line.suggested_answer_id.value
                    survey.update({line.matrix_row_id.value: answer})
                elif line.question_id.question_type in ["binary", "signature"]:
                    answer = line.answer_binary_ids[:1].value_binary
                    survey.update({line.question_id.display_name: answer})
                else:
                    answer = line.display_name
                    survey.update({line.question_id.display_name: answer})
        return survey

    def fill_survey_related_items(self, vals):
        survey = self.get_related_survey_answers()
        items = vals["items"]
        for key in items:
            item = items[key]
            placeholder = item.get("placeholder")
            if survey.get(placeholder) and item["role_id"] == self.role_id.id:
                if survey.get(placeholder) and item["field_type"] == "text":
                    item["value"] = survey.get(placeholder)
                elif survey.get(placeholder) and item["field_type"] == "check":
                    item["value"] = SurveyUtils.format_answer(survey.get(placeholder))
                elif survey.get(placeholder) and item["field_type"] == "signature":
                    item["value"] = survey.get(placeholder)
        return vals

    def get_info(self, access_token=False):
        vals = super().get_info(access_token)
        vals = self.fill_survey_related_items(vals)
        return vals
