import sys
from datetime import date, datetime
from elixr.core import AttrDict
from ..address import Country, State
from ..orgz import PartyType, EmailContact, PhoneContact, Organisation


# python version flag
py3k = sys.version_info.major > 2


ERROR_NOT_INT = 'is invalid integer'
ERROR_NOT_DATE = 'has no date in it'
ERROR_NOT_FLOAT = 'is not a float'
ERROR_NOT_BOOLEAN = 'is not a boolean'
ERROR_MISSING_REQUIRED_TEXT = 'missing required text'
ERROR_NOT_UNICODE_OR_ASCII = 'not unicode or ascii string'
ERROR_NOT_ENUM_OF = lambda e: 'is bad integer/text for enum `%s`' % e.__name__

no_data = object()
no_enum = object()


def to_text(value):
    if isinstance(value, float):
        if int(value) == value:
            value = int(value)
    try:
        value = str(value)
    except UnicodeError:
        value = None
    return value


def to_bool(value):
    if value is not None:
        if type(value) == type(True):
            return value
        elif type(value) == type(0):
            return bool(value)

        # hack: needed for py2
        elif not py3k and 'long' in str(type(value)):
            return bool(value)
        
        value = to_text(value)
        if not value:
            return None
        if value.upper() in ['TRUE', 'YES', 'T', 'Y']:
            return True
        elif value.upper() in ['FALSE', 'NO', 'F', 'N']:
            return False
    return None


def to_enum(enum_type, value):
    if value is not None:
        if type(value) == type(0) or (not py3k and 'long' in str(type(value))):
            try:
                return enum_type(value)
            except ValueError:
                return None
        value = to_text(value)
        if value and hasattr(enum_type, value):
            return enum_type[value]
    return None


class XRefResolver(object):
    """Cross Refereence Resolver. Provides a convenient means of retrieving the
    `id` for a Model given a supposedly unique filter expression.

    It helps with cases where records are identified by a unique human-friendly
    value order than their respectively numeric id values. For performance, 
    results are cached for reuse.
    """
    def __init__(self, dbsession):
        self.__dbsession = dbsession
        self.__cache = {}
    
    def resolve(self, model_type, **filters):
        key = self.get_cache_key(model_type, **filters)
        if key not in self.__cache:
            query = self.__dbsession.query(model_type.id).filter_by(**filters)
            value = query.scalar()
            if value:
                self.__cache[key] = value
        return self.__cache.get(key)
    
    def clear_cache(self):
        """Clears the cache maintained internally.
        """
        self.__cache.clear()
    
    @staticmethod
    def get_cache_key(model_type, **filters):
        pairs = ['%s=%s' % (k, filters[k]) for k in sorted(filters)]
        return ('#'.join([model_type.__name__] + pairs)).lower()


class ImporterBase(object):
    
    def __init__(self, context, progress_callback=None):
        assert 'db' in context
        assert 'cache' in context
        self.progress_callback = progress_callback
        if not isinstance(context, AttrDict):
            context = AttrDict(context)
        self.context = context
        self.errors = []
    
    def error(self, row, col, message):
        message_seq = (self.sheet_name, row, col, message)
        self.errors.append(message_seq)
    
    def resolve_xref(self, data, *xref_mapping):
        """Resolves Cross Reference records found within data using provided
        reference sources data.abs

        xref_mapping: is to be a list with items as thus:
            `(xref_field, filter_field, model_type)`
        """
        resolve = self.context.cache.resolve
        for xref_field, filter_field, model_type in xref_mapping:
            if xref_field not in data:
                continue
            xref_value = data.pop(xref_field)
            if not isinstance(xref_value, (list, tuple)):
                data[xref_field] = resolve(model_type, **{filter_field: xref_value})
            else:
                ids = [resolve(model_type, **{filter_field: v}) for v in xref_value]
                data[xref_field] = [id for id in ids if id]
        
    def progress(self, *args):
        if self.progress_callback is not None:
            self.progress_callback(*args)
    
    def is_empty_row(self, sheet, row, num_cols=30):
        # we've picked 30 as an arbitrary number of columns to test so that
        # caller doesn't specify the number.
        for col in range(1, num_cols):
            try:
                if sheet.cell(row=row, column=col).value:
                    return False
            except ValueError:
                break
        return True
    
    def get_cell_value(self, sheet, row, col, default=no_data):
        try:
            return sheet.cell(row=row, column=col).value
        except ValueError:
            if default != no_data:
                return default
            raise
    
    def get_cell_and_found(self, sheet, row, col, default=''):
        try:
            value = sheet.cell(row=row, column=col).value
            return (value, True) if value else (default, False)
        except ValueError:
            return (default, False)
    
    def get_bool_from_cell(self, sheet, row, col):
        value, found = self.get_cell_and_found(sheet, row, col)
        if not found:
            return None
        value = to_bool(value)
        if value is None:
            self.error(row, col, ERROR_NOT_BOOLEAN)
            return None
        return value
    
    def get_required_bool_from_cell(self, sheet, row, col):
        value, found = self.get_cell_and_found(sheet, row, col)
        if not value:
            self.error(row, col, ERROR_MISSING_REQUIRED_TEXT)
            return None
        return self.get_bool_from_cell(sheet, row, col)
    
    def get_date_from_cell(self, sheet, row, col, default=None):
        value, found = self.get_cell_and_found(sheet, row, col)
        if not found or value == '':
            return default
        
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        
        value = to_text(value)
        if value is not None:
            try:
                dt = [int(v) for v in value.replace('/', '-').split('-')]
                return date(*dt)
            except (TypeError, ValueError):
                self.error(row, col, ERROR_NOT_DATE)
        return None
    
    def get_required_date_from_cell(self, sheet, row, col):
        value, found = self.get_cell_and_found(sheet, row, col)
        if not found or value == '':
            self.error(row, col, ERROR_MISSING_REQUIRED_TEXT)
            return None
        return self.get_date_from_cell(sheet, row, col)
    
    def get_enum_from_cell(self, sheet, row, col, enum_type, default=no_enum):
        value, found = self.get_cell_and_found(sheet, row, col)
        if not found or value == '':
            if default is no_enum:
                self.error(row, col, ERROR_NOT_ENUM_OF(enum_type))
                return None
            return default
        value = to_enum(enum_type, value)
        if value is None:
            self.error(row, col, ERROR_NOT_ENUM_OF(enum_type))
        return value
    
    def get_required_enum_from_cell(self, sheet, row, col, enum_type):
        value, found = self.get_cell_and_found(sheet, row, col)
        if not found or value == '':
            self.error(row, col, ERROR_MISSING_REQUIRED_TEXT)
            return None
        return self.get_enum_from_cell(sheet, row, col, enum_type)

    def get_float_found_valid(self, sheet, row, col, default=0.0):
        value, found = self.get_cell_and_found(sheet, row, col, default)
        valid = True
        if isinstance(value, str) and not value.strip():
            value, found = (default, False)
        if found:
            try:
                value = float(value)
            except (TypeError, ValueError):
                self.error(row, col, ERROR_NOT_FLOAT)
                valid, value = (False, default or None)
        return (value, found, valid)
    
    def get_float_from_cell(self, sheet, row, col, default=0.0):
        value, found, valid = self.get_float_found_valid(sheet, row, col, default)
        return value
    
    def get_required_float_from_cell(self, sheet, row, col):
        value, found, valid = self.get_float_found_valid(sheet, row, col)
        if not found:
            self.error(row, col, ERROR_NOT_FLOAT)
        return value
    
    def get_id_from_cell(self, sheet, row, col, default=''):
        value, found, valid = self.get_text_found_valid(sheet, row, col, default)
        return value.strip()
    
    def get_required_id_from_cell(self, sheet, row, col):
        value, found, valid = self.get_text_found_valid(sheet, row, col)
        if valid and not value:
            self.error(row, col, ERROR_MISSING_REQUIRED_TEXT)
        return value.strip()
    
    def get_ids_from_cell(self, sheet, row, col):
        value, found, valid = self.get_text_found_valid(sheet, row, col)
        if not value:
            return []
        return [p.strip() for p in value.split(',') if p.strip()]
    
    def get_required_ids_from_cell(self, sheet, row, col):
        value, found = self.get_cell_and_found(sheet, row, col)
        if not value:
            self.error(row, col, ERROR_MISSING_REQUIRED_TEXT)
            return []
        return self.get_ids_from_cell(sheet, row, col)
    
    def get_int_found_valid(self, sheet, row, col, default=0):
        value, found = self.get_cell_and_found(sheet, row, col, default)
        valid = True
        if isinstance(value, str) and not value.strip():
            value, found = (default, False)
        if found:
            try:
                value = int(value)
            except (TypeError, ValueError):
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    pass
            if isinstance(value, float):
                if int(value) != value:
                    self.error(row, col, ERROR_NOT_INT)
                    valid = False
                else:
                    value = int(value)
            elif not isinstance(value, int):
                self.error(row, col, ERROR_NOT_INT)
                valid, value = (False, None)
        return (value, found, valid)
    
    def get_int_from_cell(self, sheet, row, col, default=0):
        value, found, valid = self.get_int_found_valid(sheet, row, col, default)
        return value
    
    def get_required_int_from_cell(self, sheet, row, col):
        value, found, valid = self.get_int_found_valid(sheet, row, col)
        if not found:
            self.error(row, col, ERROR_NOT_INT)
        return value

    def get_text_found_valid(self, sheet, row, col, default=''):
        value, found = self.get_cell_and_found(sheet, row, col, default)
        valid = True
        if found:
            value = to_text(value)
            if not value:
                self.error(row, col, ERROR_NOT_UNICODE_OR_ASCII)
                valid, value = (False, default)
        return (value, found, valid)
    
    def get_text_from_cell(self, sheet, row, col, default=''):
        value, found, valid = self.get_text_found_valid(sheet, row, col, default)
        return value
    
    def get_required_text_from_cell(self, sheet, row, col):
        value, found, valid = self.get_text_found_valid(sheet, row, col)
        if valid and not value:
            self.error(row, col, ERROR_MISSING_REQUIRED_TEXT)
        return value

    @property
    def sheet(self):
        if self.sheet_name not in self.wb.sheetnames:
            return
        return self.wb.get_sheet_by_name(self.sheet_name)
    
    def import_data(self, wb):
        self.wb = wb
        if self.sheet:
            return self.process()


class ExactTextMatcher(object):
    """Returns all texts found in `available_texts` which are exact match 
    of `target_text`.
    """
    def __call__(self, available_texts, target_text):
        target_text = target_text.strip().lower()
        return [
            t for t in available_texts 
                if target_text == t.strip().lower()
        ]


class PrefixedTextMatcher(object):
    """Returns all texts found in `available_texts` which all start with
    `target_text` followed by some other text.
    """
    def __call__(self, available_texts, target_text):
        target_text = target_text.strip().lower()
        return [
            t for t in available_texts
                if t.strip().lower().startswith(target_text)
        ]


class SuffixedTextMatcher(object):
    """Returns all texts found in `available_texts` which all end with
    `target_text` and might have some other text in-front.abs
    """
    def __call__(self, available_texts, target_text):
        target_text = target_text.strip().lower()
        return [
            t for t in available_texts
                if t.strip().lower().endswith(target_text)
        ]


class MegaImporterBase(object):
    """Defines a base implementation for managing a collection of `importers`
    to pull in data from an excel file into a database.
    """
    def __init__(self, context, matcher=None):
        assert 'db' in context
        if not isinstance(context, AttrDict):
            context = AttrDict(context)
        self.matcher =  matcher or PrefixedTextMatcher()
        self.context = context
        self.errors = []
    
    @property
    def has_errors(self):
        return len(self.errors) > 0
    
    @property
    def importers(self):
        message = 'Needs to be overriden by derived classes.'
        raise NotImplementedError(message)
    
    def import_data(self, wb, progress_callback=None):
        matcher = self.matcher
        available_sheets = wb.get_sheet_names()
        for importer in self.importers:
            target_name = importer.sheet_name
            matches = matcher(available_sheets, target_name)
            for sheet_name in sorted(matches):
                importer.sheet_name = sheet_name
                imp = importer(self.context, progress_callback)
                imp.import_data(wb)
                self.errors.extend(imp.errors)
            
            # restore original sheet_name for importer
            importer.sheet_name = target_name
        
        if self.errors:
            self.context.db.rollback()
    
    def summarise_errors(self):
        errors = {}
        for sheet_name, row, col, message in self.errors:
            sheet_errors = errors.setdefault(sheet_name, {})
            sheet_errors.setdefault(message, []).append((col, row))
        
        error_lines = []
        for sheet_name, message_errors in sorted(errors.items()):
            if error_lines:
                error_lines.append('')
            error_lines.append(sheet_name)
            error_lines.append('-' * len(sheet_name))
            for message, cells in sorted(message_errors.items()):
                col_rows = []
                current_col, start, end = -1, 0, 0
                for col, row in sorted(cells):
                    if col != current_col or row > end + 1:
                        if current_col > -1:
                            col_rows.append((current_col, start, end))
                        current_col, start = col, row
                    end = row
                col_rows.append((current_col, start, end))
                error_lines.append('')
                error_lines.append(message + ':')

                error_cells = []
                for col, start, end in col_rows:
                    cell = chr(col + ord('A') - 1)
                    if start == end:
                        cell += '%s' % start
                    else:
                        cell += '%s-%s' % (start, end)
                    error_cells.append(cell)
                error_lines.append(', '.join(error_cells))
        return '\n'.join(error_lines)
    
    @classmethod
    def make_for_exact_match(cls, context):
        return cls(context, ExactTextMatcher())
    
    @classmethod
    def make_for_prefix_match(cls, context):
        return cls(context, PrefixedTextMatcher())
    
    @classmethod
    def make_for_suffix_match(cls, context):
        return cls(context, SuffixedTextMatcher())


class AdminBoundaryImporter(ImporterBase):
    """An importer able to proces and import Country and State data from an
    excel file.
    """
    sheet_name = 'admin-boundaries'

    def __init__(self, context, progress_callback=None):
        assert 'db' in context
        assert 'cache' in context
        super(AdminBoundaryImporter, self).__init__(context, progress_callback)
    
    def create_country(self, row, data):
        try:
            country = Country(**data)
            self.context.db.add(country)
        except Exception as ex:
            message_fmt = 'Country could not be created. Err: %s'
            self.error(row, 0, message_fmt % str(ex))
    
    def create_state(self, row, data):
        self.resolve_xref(data, ('country_id', 'code', Country))
        try:
            state = State(**data)
            self.context.db.add(state)
        except Exception as ex:
            message_fmt = 'State could not be created. Err: %s'
            self.error(row, 0, message_fmt % str(ex))
    
    def import_country(self, sh, row):
        row, nrows = (row + 2, sh.max_row)
        num_errors = len(self.errors)
        while row <= nrows:
            if self.is_empty_row(sh, row):
                break
            
            data = AttrDict()
            data['code'] = self.get_required_id_from_cell(sh, row, 1)
            data['name'] = self.get_required_text_from_cell(sh, row, 2)
            if num_errors < len(self.errors):
                break
            self.create_country(row, data)
            self.progress(row, nrows)
            row += 1
        return (row + 1)
    
    def import_state(self, sh, row):
        row, nrows = (row + 2, sh.max_row)
        num_errors = len(self.errors)
        while row <= nrows:
            if self.is_empty_row(sh, row):
                break
            
            data = AttrDict()
            data['code'] = self.get_required_id_from_cell(sh, row, 1)
            data['name'] = self.get_required_text_from_cell(sh, row, 2)
            data['country_id'] = self.get_required_id_from_cell(sh, row, 3)
            if num_errors < len(self.errors):
                break
            self.create_state(row, data)
            self.progress(row, nrows)
            row += 1
        return (row + 1)
        
    def process(self):
        sh, row, nrows = (self.sheet, 1, self.sheet.max_row)
        ## flags are provided in reverse order as `list.pop` operates
        ## on items from the bottom NOT the top
        flags = ['states', 'countries']
        while row <= nrows:
            if not flags: break
            if self.is_empty_row(sh, row):
                row += 1; continue
            
            value = sh.cell(row=row, column=1).value
            if value not in flags:
                row += 1; continue
            
            while value != flags.pop(): 
                pass # keep popping ;-)
            
            if value == 'countries':
                row = self.import_country(sh, row)
            elif value == 'states':
                row = self.import_state(sh, row)
        self.progress(row, nrows)


class PartyImporterBase(ImporterBase):
    """Base importer to pull excel data into a database for models derived
    from the Party model.
    """
    subtype = None

    def process_chunk(self, row, col, data):
        sh = self.sheet
        data['name'] = self.get_required_text_from_cell(sh, row, col)
        data['addr_street'] = self.get_text_from_cell(sh, row, col+1)
        data['addr_town'] = self.get_text_from_cell(sh, row, col+2)
        data['addr_state_id'] = self.get_required_id_from_cell(sh, row, col+3)
        data['addr_landmark'] = self.get_text_from_cell(sh, row, col+4)
        data['postal_code'] = self.get_text_from_cell(sh, row, col+5)
        return col+5
    
    def create_item(self, row, data):
        raise NotImplementedError()
    
    def add_item(self, row, item):
        raise NotImplementedError()
    
    def post_process(self):
        pass
    
    def process(self):
        sh, nrows = (self.sheet, self.sheet.max_row)
        for row in range(2, nrows + 1):
            data = AttrDict()
            num_errors = len(self.errors)
            self.process_chunk(row, 1, data)
            if num_errors == len(self.errors):
                item = self.create_item(row, data)
                self.add_item(row, item)
                self.progress(row, nrows)
        self.post_process()
        self.progress(row, nrows)


class OrganisationImporter(PartyImporterBase):
    """An importer to process and import Organisation data from an excel file.
    """
    IGNORE_REQ = '-x-'
    sheet_name = 'organisations'
    subtype = PartyType.organisation
    fncode_type = None

    def __init__(self, context, progress_callback=None):
        super(OrganisationImporter, self).__init__(context, progress_callback)
        self.__root = context.db.query(Organisation).first()
        assert self.fncode_type != None
    
    def add_item(self, row, item):
        if not item: return
        # be sure only single root exists
        if not item.parent and not item.parent_id:
            if self.__root:
                message = 'Root organisation already exists.'
                self.error(row, 0, message)
                return
            else:
                self.__root = item
        
        # all is good at this point
        self.context.db.add(item)
    
    def create_item(self, row, data):
        # extract contact fields
        contacts = []
        for email in (data.pop('emails') or []):
            contacts.append(EmailContact(address=email))
        for number in (data.pop('phones') or []):
            contacts.append(PhoneContact(number=number))
        
        self.resolve_xref(data, 
            ('addr_state_id', 'code', State),
            ('parent_id', 'short_name', Organisation))
        data.fncode = data.fncode.value     # norm into int
        try:
            item = Organisation(**data)
            if contacts:
                item.contacts.extend(contacts)
            return item
        except Exception as ex:
            message_fmt = 'Organisation could not be created. Err: %s'
            self.error(row, 0, message_fmt % str(ex))
        return None
    
    def post_process(self):
        pass

    def process_chunk(self, row, col, data):
        sh, ftype = (self.sheet, self.fncode_type)
        data['parent_id'] = self.get_required_id_from_cell(sh, row, col)
        data['identifier'] = self.get_required_id_from_cell(sh, row, col+1)
        data['fncode'] = self.get_required_enum_from_cell(sh, row, col+2, ftype)
        data['short_name'] = self.get_text_from_cell(sh, row, col+3)
        ## break-out to capture party chunk
        col = super(OrganisationImporter, self).process_chunk(row, col+4, data)
        ## return to normal flow
        data['website_url'] = self.get_text_from_cell(sh, row, col+1)
        data['emails'] = self.get_ids_from_cell(sh, row, col+2)
        data['phones'] = self.get_ids_from_cell(sh, row, col+3)
        data['date_established'] = self.get_date_from_cell(sh, row, col+4)
        data['description'] = self.get_text_from_cell(sh, row, col+5)
        data['longitude'] = self.get_float_from_cell(sh, row, col+6)
        data['latitude'] = self.get_float_from_cell(sh, row, col+7)
        data['altitude'] = self.get_float_from_cell(sh, row, col+8)
        data['gps_error'] = self.get_float_from_cell(sh, row, col+9)
        return col+12
