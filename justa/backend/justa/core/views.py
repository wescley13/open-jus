from django.core.paginator import Paginator
from restless.dj import DjangoResource
from restless.exceptions import BadRequest
from restless.preparers import FieldsPreparer

from justa.core.models import CourtOrder
from justa.core.forms import AuthenticationForm, CourtOrderForm


class CourtOrderResource(DjangoResource):
    page_size = 25
    preparer = FieldsPreparer(fields={
        f.name: f.name
        for f in CourtOrder._meta.fields
    })

    def serialize_list(self, data):
        if data is None:
            return super(DjangoResource, self).serialize_list(data)

        paginator = Paginator(data, self.page_size)
        page_number = self.request.GET.get('page', 1)
        if page_number not in paginator.page_range:
            raise BadRequest('Invalid page number')

        self.page = paginator.page(page_number)
        data = self.page.object_list
        return super(DjangoResource, self).serialize_list(data)

    def wrap_list_response(self, data):
        response_dict = super(DjangoResource, self).wrap_list_response(data)

        if not hasattr(self, 'page'):
            return response_dict

        next_page, previous_page = None, None
        if self.page.has_next() and self.page.next_page_number():
            next_page = True
        if self.page.has_previous() and self.page.previous_page_number():
            previous_page = True

        response_dict['pagination'] = {
            'num_pages': self.page.paginator.num_pages,
            'count': self.page.paginator.count,
            'page': self.page.number,
            'start_index': self.page.start_index(),
            'end_index': self.page.end_index(),
            'next_page': next_page,
            'previous_page': previous_page,
            'per_page': self.page.paginator.per_page,
        }
        return response_dict

    def is_authenticated(self):
        if self.endpoint in {'list', 'detail'}:
            return True

        form = AuthenticationForm(self.request.POST)
        return form.is_valid()

    def list(self):
        return CourtOrder.objects.all()

    def detail(self, pk):
        return CourtOrder.objects.get(id=pk)

    def create(self):
        form = CourtOrderForm(self.data)
        if not form.is_valid():
            raise BadRequest(form.errors)

        return form.save()
