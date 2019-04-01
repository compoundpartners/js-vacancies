from aldryn_client import forms

class Form(forms.BaseForm):

    summary_richtext = forms.CheckboxField(
        "Use rich text for Summary",
        required=False,
        initial=False)

    def to_settings(self, data, settings):

        if data['summary_richtext']:
            settings['VACANCIES_SUMMARY_RICHTEXT'] = int(data['summary_richtext'])

        return settings
