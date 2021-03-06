#    Copyright 2015 SimpliVity Corp.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock

from cinder import context
from cinder import objects
from cinder.tests.unit import fake_volume
from cinder.tests.unit import objects as test_objects


class TestVolume(test_objects.BaseObjectsTestCase):
    def setUp(self):
        super(TestVolume, self).setUp()
        # NOTE (e0ne): base tests contains original RequestContext from
        # oslo_context. We change it to our RequestContext implementation
        # to have 'elevated' method
        self.context = context.RequestContext(self.user_id, self.project_id,
                                              is_admin=False)

    @staticmethod
    def _compare(test, db, obj):
        for field, value in db.items():
            if not hasattr(obj, field):
                continue

            test.assertEqual(db[field], obj[field])

    @mock.patch('cinder.db.volume_glance_metadata_get', return_value={})
    @mock.patch('cinder.db.volume_get')
    def test_get_by_id(self, volume_get, volume_glance_metadata_get):
        db_volume = fake_volume.fake_db_volume()
        volume_get.return_value = db_volume
        volume = objects.Volume.get_by_id(self.context, 1)
        self._compare(self, db_volume, volume)

    @mock.patch('cinder.db.volume_create')
    def test_create(self, volume_create):
        db_volume = fake_volume.fake_db_volume()
        volume_create.return_value = db_volume
        volume = objects.Volume(context=self.context)
        volume.create()
        self.assertEqual(db_volume['id'], volume.id)

    @mock.patch('cinder.db.volume_metadata_get', return_value={})
    @mock.patch('cinder.db.volume_get')
    def test_refresh(self, volume_get, volume_metadata_get):
        db_volume = fake_volume.fake_db_volume()
        volume_get.return_value = db_volume
        volume = objects.Volume.get_by_id(self.context, '1')
        volume.refresh()
        volume_get.assert_has_calls([mock.call(self.context, '1'),
                                     mock.call(self.context, '1')])
        self._compare(self, db_volume, volume)

    @mock.patch('cinder.db.volume_update')
    def test_save(self, volume_update):
        db_volume = fake_volume.fake_db_volume()
        volume = objects.Volume._from_db_object(self.context,
                                                objects.Volume(), db_volume)
        volume.display_name = 'foobar'
        volume.save()
        volume_update.assert_called_once_with(self.context, volume.id,
                                              {'display_name': 'foobar'})

    @mock.patch('cinder.db.volume_destroy')
    def test_destroy(self, volume_destroy):
        db_volume = fake_volume.fake_db_volume()
        volume = objects.Volume._from_db_object(self.context,
                                                objects.Volume(), db_volume)
        volume.destroy()
        self.assertTrue(volume_destroy.called)
        admin_context = volume_destroy.call_args[0][0]
        self.assertTrue(admin_context.is_admin)

    def test_obj_fields(self):
        volume = objects.Volume(context=self.context, id=2, _name_id=2)
        self.assertEqual(['name', 'name_id'], volume.obj_extra_fields)
        self.assertEqual('volume-2', volume.name)
        self.assertEqual('2', volume.name_id)

    def test_obj_field_previous_status(self):
        volume = objects.Volume(context=self.context,
                                previous_status='backing-up')
        self.assertEqual('backing-up', volume.previous_status)


class TestVolumeList(test_objects.BaseObjectsTestCase):
    @mock.patch('cinder.db.volume_glance_metadata_get', return_value={})
    @mock.patch('cinder.db.volume_get_all')
    def test_get_all(self, volume_get_all, volume_glance_metadata_get):
        db_volume = fake_volume.fake_db_volume()
        volume_get_all.return_value = [db_volume]

        volumes = objects.VolumeList.get_all(self.context,
                                             mock.sentinel.marker,
                                             mock.sentinel.limit,
                                             mock.sentinel.sort_key,
                                             mock.sentinel.sort_dir)
        self.assertEqual(1, len(volumes))
        TestVolume._compare(self, db_volume, volumes[0])

    @mock.patch('cinder.db.volume_get_all_by_host')
    def test_get_by_host(self, get_all_by_host):
        db_volume = fake_volume.fake_db_volume()
        get_all_by_host.return_value = [db_volume]

        volumes = objects.VolumeList.get_all_by_host(
            self.context, 'fake-host')
        self.assertEqual(1, len(volumes))
        TestVolume._compare(self, db_volume, volumes[0])

    @mock.patch('cinder.db.volume_get_all_by_group')
    def test_get_by_group(self, get_all_by_group):
        db_volume = fake_volume.fake_db_volume()
        get_all_by_group.return_value = [db_volume]

        volumes = objects.VolumeList.get_all_by_group(
            self.context, 'fake-host')
        self.assertEqual(1, len(volumes))
        TestVolume._compare(self, db_volume, volumes[0])

    @mock.patch('cinder.db.volume_get_all_by_project')
    def test_get_by_project(self, get_all_by_project):
        db_volume = fake_volume.fake_db_volume()
        get_all_by_project.return_value = [db_volume]

        volumes = objects.VolumeList.get_all_by_project(
            self.context, mock.sentinel.project_id, mock.sentinel.marker,
            mock.sentinel.limit, mock.sentinel.sorted_keys,
            mock.sentinel.sorted_dirs, mock.sentinel.filters)
        self.assertEqual(1, len(volumes))
        TestVolume._compare(self, db_volume, volumes[0])
