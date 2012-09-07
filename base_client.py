import urllib
import urllib2
import logging

import json

logger = logging.getLogger(__name__)

CONTACT_PARAMS = {
    'name': '',
    'last_name': '',
    'first_name': '',
    'is_organisation': '',
    'contact_id': '',
    'email': '',
    'phone': '',
    'mobile': '',
    'twitter': '',
    'skype': '',
    'facebook': '',
    'linkedin': '',
    'address': '',
    'city': '',
    'country': '',
    'title': '',
    'description': '',
    'industry': '',
    'website': '',
    'fax': '',
    'tag_list': '',
    'private': '',
}

DEAL_PARAMS = {
    'name': '',
    'entity_id': '',
    'scope': '',
    'hot': 'false',
    'deal_tags': '',
    'contact_ids': '',
    'source_id': '',
    'stage': '',
}

DEAL_STAGES = [
    'incoming',
    'qualified',
    'quote',
    'custom1',
    'custom2',
    'custom3',
    'closure',
    'won',
    'lost',
    'unqualified',
]


def _unicode_dict(d):
    new_dict = {}
    for k, v in d.iteritems():
        new_dict[k] = unicode(v).encode('utf-8')
    return new_dict


class BaseAPIService(object):

    def __init__(self, email, password, format='json'):
        """
        Gets a login token for base, and set the format for response objects.
        format =    'json' (default)
                    'xml'
        """
        self.base_url = 'https://sales.futuresimple.com/api/v1/'

        if format == 'json':
            self.format = '.json'
        elif format == 'xml':
            self.format = '.xml'

        # Get token
        status, self.token = self._get_login_token(email=email, password=password)
        if status == "ERROR":
            # If we get an error, return it.
            logger.error(self.token)
            self.auth_failed = True
        else:
            # Set URL header for future requests
            self.header = {"X-Pipejump-Auth": self.token}
            self.auth_failed = False

    ##########################
    # Token Functions
    ##########################
    def _get_login_token(self, email, password):
        """
        Passes email and password to base api and returns login token.
        """
        auth_url = 'authentication.json'
        params = urllib.urlencode({
            'email': email,
            'password': password,
        })

        try:
            data = urllib2.urlopen(self.base_url + auth_url, params).read()
        except urllib2.HTTPError, e:
            return ("ERROR", "HTTP: %s" % str(e))
        except urllib2.URLError, e:
            return ("ERROR", "Error URL: %s" % str(e.reason.args[1]))

        try:
            dict_data = json.loads(data)
            token = dict_data["authentication"]["token"]
        except KeyError:
            return ("ERROR", "Error: No Token Returned")

        return ("SUCCESS", token)

    ##########################
    # Accounts Functions
    ##########################
    def get_accounts(self):
        """
        Get current account.
        """
        account_url = 'account' + self.format

        url = self.base_url + account_url

        req = urllib2.Request(url, headers=self.header)
        response = urllib2.urlopen(req)
        data = response.read()

        return data

    ##########################
    # Deals Functions
    ##########################
    def get_deals(self, page=1, stage='incoming'):
        """
        Gets deal objects in batches of 20.
        Arguments:
            page = the set of deals to return. 1 (default) returns the first 20.
            stage = the stage of deals to return - see DEAL_STAGES list for details.
        """
        deals_url = 'deals' + self.format
        url = self.base_url + deals_url
        params = urllib.urlencode({
            'page': page,
            'stage': stage,
        })

        full_url = url + '?' + params

        req = urllib2.Request(full_url, headers=self.header)
        response = urllib2.urlopen(req)
        data = response.read()

        return data

    def create_deal(self, deal_info):
        """
        Creates a new deal in base, given proper deal parameters in deal_info argument.
        Proper parameters are shown in the DEAL_PARAMS dictionary.
        Returns a json or xml reponse.
        """
        return self._post_deal(deal_info=deal_info)

    def update_deal(self, deal_info, deal_id):
        """
        Updates a deal with the given the base deal_id accoring to deal_info parameters.
        Proper parameters are shown in the DEAL_PARAMS dictionary.
        Returns a json or xml response.
        """
        return self._post_deal(deal_info=deal_info, deal_id=deal_id)

    def _post_deal(self, deal_info={}, deal_id=None):
        """
        PRIVATE FUNCTION:
        Creates a new deal if deal_id = None.
        Otherwise, edits the deal with the given deal_id.
        """

        deals_url = 'deals'
        if deal_id != None:
            deals_url += '/%s' % str(deal_id)
        deals_url += self.format

        url = self.base_url + deals_url

        if deal_info == {} or (('name' not in deal_info.keys() \
                or 'entity_id' not in deal_info.keys()) and deal_id == None):
            return "Missing required attributes 'name' or 'entity_id'"

        final_params = {}

        for key in deal_info.keys():
            if key not in DEAL_PARAMS.keys():
                return "%s is not a legal deal attribute" % key
            else:
                final_params[key] = deal_info[key]

        params = urllib.urlencode(_unicode_dict(final_params))

        req = urllib2.Request(url, data=params, headers=self.header)
        if deal_id != None:
            req.get_method = lambda: 'PUT'
        response = urllib2.urlopen(req)
        data = response.read()

        return data

    def create_deal_note(self, deal_id, note_content):
        """
        Creates a note associated with a specific deal (defined by Base's unique deal_id)
        with the content note_content.
        Returns a json or xml response.
        """
        return self._post_deal_note(deal_id=deal_id, note_content=note_content)

    def update_deal_note(self, deal_id, note_content, note_id):
        """
        Edits a note (defined by Base's unique deal_id and the note's unique note_id)
        with the content note_content.
        Returns a json or xml response.
        """
        return self._post_deal_note(deal_id=deal_id, note_content=note_content, note_id=note_id)

    def _post_deal_note(self, deal_id, note_content='', note_id=None):
        """
        PRIVATE FUNCTION
        Creates a new note for a given deal_id with content note_content, if note_id == None.
        Otherwise, edits the note with the given note_id.
        """

        url_base_template = 'deals/%s/notes' % str(deal_id)
        if note_id != None:
            url_base_template += '/%s' % str(note_id)
        url_base_template += self.format

        url = self.base_url + url_base_template

        params = urllib.urlencode({'note[content]': unicode(note_content).encode('utf-8')})

        req = urllib2.Request(url, data=params, headers=self.header)
        if note_id != None:
            req.get_method = lambda: 'PUT'
        response = urllib2.urlopen(req)
        data = response.read()

        return data

    ##########################
    # Contact Functions
    ##########################
    def get_contacts(self, page=1):
        """
        Gets contact objects.
        """
        contacts_url = 'contacts' + self.format
        url = self.base_url + contacts_url
        params = urllib.urlencode({
            'page': page,
        })
        # Append parameters
        full_url = url + '?' + params

        req = urllib2.Request(full_url, headers=self.header)
        response = urllib2.urlopen(req)
        data = response.read()

        return data

    def create_contact(self, contact_info, person=True):
        """
        Creates a new contact based on contact_info with fields shown in CONTACT_PARAMS.
        Assumes the contact is a person.  If the contact is a company, use person=False
        Returns a json or xml response.
        """
        return self._post_contact(contact_info=contact_info, contact_id=None, person=person)

    def update_contact(self, contact_info, contact_id, person=True):
        """
        Edits contact with the unique base_id based on contact_info with fields shown in CONTACT_PARAMS.
        Assumes the contact is a person.  If the contact is a company, use person=False
        Returns a json or xml response.
        """
        return self._post_contact(contact_info=contact_info, contact_id=contact_id, person=person)

    def _post_contact(self, contact_info={}, contact_id=None, person=True):
        """
        Creates a new contact if contact_id == None.
        Otherwise, edits contact with the given id.
        """
        contacts_url = 'contacts'
        if contact_id != None:
            contacts_url += '/%s' % str(contact_id)
        contacts_url += self.format

        url = self.base_url + contacts_url

        CONTACT_PARAMS['is_organisation'] = 'false'
        if not person:
            CONTACT_PARAMS['is_organisation'] = 'true'

        if contact_info == {} or \
                ('name' not in contact_info.keys() and 'last_name' not in contact_info.keys()):
            return

        final_params = {}

        for key in contact_info.keys():
            if key not in CONTACT_PARAMS.keys():
                return
            else:
                final_params['contact[' + key + ']'] = contact_info[key]

        params = urllib.urlencode(_unicode_dict(final_params))

        req = urllib2.Request(url, data=params, headers=self.header)

        if contact_id != None:
            req.get_method = lambda: 'PUT'
        response = urllib2.urlopen(req)
        data = response.read()

        return data

    def create_contact_note(self, contact_id, note_content):
        """
        Creates a note associated with a specific contact (defined by Base's unique contact_id)
        with the content note_content.
        Returns a json or xml response.
        """
        return self._post_contact_note(contact_id=contact_id, note_content=note_content)

    def update_contact_note(self, contact_id, note_content, note_id):
        """
        Edits a note (defined by Base's unique contact_id and the note's unique note_id)
        with the content note_content.
        Returns a json or xml response.
        """
        return self._post_contact_note(contact_id=contact_id, note_content=note_content, note_id=note_id)

    def _post_contact_note(self, contact_id, note_content='', note_id=None):
        """
        PRIVATE FUNCTION
        Creates a new note for a given contact_id with content note_content, if note_id == None.
        Otherwise, edits the note with the given note_id.
        """

        url_base_template = 'contacts/%s/notes' % str(contact_id)
        if note_id != None:
            url_base_template += '/%s' % str(note_id)
        url_base_template += self.format

        url = self.base_url + url_base_template

        params = urllib.urlencode({'note[content]': unicode(note_content).encode('utf-8')})

        req = urllib2.Request(url, data=params, headers=self.header)
        if note_id != None:
            req.get_method = lambda: 'PUT'
        response = urllib2.urlopen(req)
        data = response.read()

        return data

    ##########################
    # Sources Functions
    ##########################
    def get_sources(self, other=0):
        """
        Gets deal sources.
        Argument:
            other: default to 0.  If 1, retrieves sources added by other users in the account.
        """
        sources_url = 'sources' + self.format
        url = self.base_url + sources_url
        if other == 1:
            params = urllib.urlencode({
                'other': other,
            })
        else:
            params = ''
        # Append parameters
        full_url = url + '?' + params

        req = urllib2.Request(full_url, headers=self.header)
        response = urllib2.urlopen(req)
        data = response.read()

        return data