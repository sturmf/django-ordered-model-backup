from functools import update_wrapper

# from django.conf import settings
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
# from django.utils.html import strip_spaces_between_tags as short
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string
from django.contrib import admin
from django.contrib.admin.util import unquote
from django.contrib.admin.views.main import ChangeList


class OrderedModelAdmin(admin.ModelAdmin):

    def get_model_info(self):
        return dict(app=self.model._meta.app_label,
                    model=self.model._meta.module_name)

    def get_urls(self):
        from django.conf.urls import patterns, url

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        return patterns('',
                        url(r'^(.+)/move-(up)/$', wrap(self.move_view),
                            name='{app}_{model}_order_up'.format(**self.get_model_info())),

                        url(r'^(.+)/move-(down)/$', wrap(self.move_view),
                            name='{app}_{model}_order_down'.format(**self.get_model_info())),
                        ) + super(OrderedModelAdmin, self).get_urls()

    def _get_changelist(self, request):
        list_display = self.get_list_display(request)
        list_display_links = self.get_list_display_links(request, list_display)

        cl = ChangeList(request, self.model, list_display,
                        list_display_links, self.list_filter, self.date_hierarchy,
                        self.search_fields, self.list_select_related,
                        self.list_per_page, self.list_max_show_all, self.list_editable,
                        self)

        return cl

    request_query_string = ''

    def changelist_view(self, request, extra_context=None):
        cl = self._get_changelist(request)
        self.request_query_string = cl.get_query_string()
        return super(OrderedModelAdmin, self).changelist_view(request, extra_context)

    def move_view(self, request, object_id, direction):
        cl = self._get_changelist(request)
        qs = cl.get_query_set(request)

        obj = get_object_or_404(self.model, pk=unquote(object_id))
        obj.move(direction, qs)

        return HttpResponseRedirect('../../%s' % self.request_query_string)

    def move_up_down_links(self, obj):
        return render_to_string("ordered_model/admin/order_controls.html", {
            'app_label': self.model._meta.app_label,
            'module_name': self.model._meta.module_name,
            'object_id': obj.id,
            'urls': {
                'up': reverse("admin:{app}_{model}_order_up".format(**self.get_model_info()), args=[obj.id, 'up']),
                'down': reverse("admin:{app}_{model}_order_down".format(**self.get_model_info()), args=[obj.id, 'down']),
            },
            'query_string': self.request_query_string
        })
    move_up_down_links.allow_tags = True
    move_up_down_links.short_description = _(u'Move')


class OrderedTabularInline(admin.TabularInline):

    ordering = None
    list_display = ('__str__',)
    list_display_links = ()
    list_filter = ()
    list_select_related = False
    list_per_page = 100
    list_max_show_all = 200
    list_editable = ()
    search_fields = ()
    date_hierarchy = None
    paginator = Paginator

    @classmethod
    def get_model_info(cls):
        return dict(app=cls.model._meta.app_label,
                    model=cls.model._meta.module_name)

    @classmethod
    def get_urls(cls, model_admin):
        from django.conf.urls import patterns, url

        def wrap(view):
            def wrapper(*args, **kwargs):
                return model_admin.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        return patterns('',
                        url(r'^(.+)/{model}/(.+)/move-(up)/$'.format(**cls.get_model_info()), wrap(cls.move_view),
                            name='{app}_{model}_order_up_inline'.format(**cls.get_model_info())),

                        url(r'^(.+)/{model}/(.+)/move-(down)/$'.format(**cls.get_model_info()), wrap(cls.move_view),
                            name='{app}_{model}_order_down_inline'.format(**cls.get_model_info())),
                        ) # + super(OrderedTabularInline, cls).get_urls()

    @classmethod
    def get_list_display(cls, request):
        """
        Return a sequence containing the fields to be displayed on the
        changelist.
        """
        return cls.list_display

    @classmethod
    def get_list_display_links(cls, request, list_display):
        """
        Return a sequence containing the fields to be displayed as links
        on the changelist. The list_display parameter is the list of fields
        returned by get_list_display().
        """
        if cls.list_display_links or not list_display:
            return cls.list_display_links
        else:
            # Use only the first item in list_display as link
            return list(list_display)[:1]

    @classmethod
    def _get_changelist(cls, request):
        list_display = cls.get_list_display(request)
        list_display_links = cls.get_list_display_links(request, list_display)

        cl = ChangeList(request, cls.model, list_display,
                        list_display_links, cls.list_filter, cls.date_hierarchy,
                        cls.search_fields, cls.list_select_related,
                        cls.list_per_page, cls.list_max_show_all, cls.list_editable,
                        cls)

        return cl

    request_query_string = ''

    @classmethod
    def changelist_view(cls, request, extra_context=None):
        cl = cls._get_changelist(request)
        cls.request_query_string = cl.get_query_string()
        return super(OrderedTabularInline, cls).changelist_view(request, extra_context)

    @classmethod
    def queryset(cls, request):
        """
        Returns a QuerySet of all model instances that can be edited by the
        admin site. This is used by changelist_view.
        """
        qs = cls.model._default_manager.get_query_set()
        # TODO: this should be handled by some parameter to the ChangeList.
        ordering = cls.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    @classmethod
    def get_ordering(cls, request):
        """
        Hook for specifying field ordering.
        """
        return cls.ordering or ()  # otherwise we might try to *None, which is bad ;)

    @classmethod
    def get_paginator(cls, request, queryset, per_page, orphans=0, allow_empty_first_page=True):
        return cls.paginator(queryset, per_page, orphans, allow_empty_first_page)

    @classmethod
    def move_view(cls, request, admin_id, object_id, direction):
        cl = cls._get_changelist(request)
        qs = cl.get_query_set(request)

        obj = get_object_or_404(cls.model, pk=unquote(object_id))
        obj.move(direction, qs)

        return HttpResponseRedirect('../../../%s' % cls.request_query_string)

    def move_up_down_links(self, obj):
        if obj.id:
            return render_to_string("ordered_model/admin/order_controls.html", {
                'app_label': self.model._meta.app_label,
                'module_name': self.model._meta.module_name,
                'object_id': obj.id,
                'urls': {
                    'up': reverse("admin:{app}_{model}_order_up_inline".format(**self.get_model_info()), args=[obj._get_order_with_respect_to().id, obj.id, 'up']),
                    'down': reverse("admin:{app}_{model}_order_down_inline".format(**self.get_model_info()), args=[obj._get_order_with_respect_to().id, obj.id, 'down']),
                },
                'query_string': self.request_query_string
            })
        else:
            return ''
    move_up_down_links.allow_tags = True
    move_up_down_links.short_description = _(u'Move')






