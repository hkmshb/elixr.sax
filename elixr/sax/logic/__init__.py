"""Business logic definitions for elixr.sax.
"""
import re


class ActionError(Exception):
    """The base exception for all logic action related errors. It is also the
    exception thrown when an Invalid operation is initiated within an action.
    """

    def __init__(self, message=''):
        self.message = message
        super(ActionError, self).__init__(message)

    def __str__(self):
        return self.message


class NotFoundError(ActionError):
    """Exception raised by logic functions when a given object is not found.
    """
    pass


class MultipleResultsError(ActionError):
    """Exception raised by logic functions when multiple records are found
    when only one is expected.
    """
    pass


class ValidationError(ActionError):
    """Exception raise by logic function when validation of given data_dict
    fails.
    """
    def __init__(self, error_dict, error_summary=None, extra_msg=None):
        if not isinstance(error_dict, dict):
            error_dict = {'message': error_dict}
        self.error_dict = error_dict
        self._error_summary = error_summary
        super(ValidationError, self).__init__(extra_msg)

    @property
    def error_summary(self):
        """Autogenerate the summary if not supplied
        """
        def summarise(error_dict):
            """Do some i18n stuff on the error_dict keys.
            """
            def prettify(field_name):
                field_name = re.sub('(?<!\w)[Uu]rl(?!\w)', 'URL',
                                    field_name.replace('_', ' ').capitalize())
                return _(field_name.replace('_', ' '))

            summary = {}
            for key, error in error_dict.iteritems():
                summary[_(prettify(key))] = error[0]
            return summary

        if self._error_summary:
            return self._error_summary
        return summarise(self.error_dict)

    def __str__(self):
        err_msgs = (super(ValidationError, self).__str__(),
                    self.error_dict)
        return ' - '.join([str(err_msg) for err_msg in err_msgs if err_msg])
