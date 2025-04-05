1.  Go to Sign \> Settings \> Roles and create a new one with the following data if not
    there:

    - For the survey participant

      - Partner type: Expression
      - Expression: {{object.partner_id.id}}

    - For the survey responsible if you want

      - Partner type: Expression
      - Expression: {{object.survey_id.user_id.partner_id.id}}

2.  Go to Sign \> Settings \> Fields and create a new one with the following data if not
    there:

    - Text Survey Field

      - Field Type: text
      - Default Value: survey

    - Check Survey Field
      - Field Type: check
      - Default Value: survey

3.  Go to Sign \> Templates and create a template with the following data:

    - Model: Survey User Input
    - In some of the elements you will have to set the previously created role[s].

4.  Go to Settings \> Survey Sign OCA:

5.  Defines the template previously created (optional, only for automatic creation of
    signature requests).
