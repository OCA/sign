# Copyright 2026 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from .common import Common


class TestReport(Common):
    def test_multi_serial(self):
        """The Report can be printed when a request line has multiple lots."""
        # Arrange
        self.env.company.ppe_report_show_sn = True
        request = self.ppe_sn_request
        request.accept_request()
        request.picking_ids.button_validate()
        lots = request.line_ids.move_ids.lot_ids
        # pre-condition
        self.assertGreater(len(lots), 1)

        # Act
        report_content, _type = self.report._render_qweb_pdf(
            self.report.report_name, request.ids
        )

        # Assert
        report_content = report_content.decode()
        for lot in lots:
            self.assertIn(lot.name, report_content)
