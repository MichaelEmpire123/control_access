"""
Тестовый скрипт для проверки API
Запуск: python tests/run_tests.py
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Добавляем путь к проекту
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Настройка Django окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'control.settings')

import django

django.setup()

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import connection

from pilot.models import (
    User, Contractor, ComplianceDocument,
    ContractorEmployee, AccessPass, Blacklist
)
from pilot.services.contractor_service import ContractorService
from pilot.services.document_service import DocumentService
from pilot.services.access_pass_service import AccessPassService
from pilot.services.blacklist_service import BlacklistService

User = get_user_model()


class Color:
    """Цвета для вывода в консоль"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


class APITester:
    """Класс для тестирования API"""

    def __init__(self, base_url='http://localhost:8000/api/v1'):
        self.base_url = base_url
        self.token = None
        self.refresh_token = None
        self.test_data = {}
        self.results = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        self._ensure_server_running()

    def _ensure_server_running(self):
        """Проверка доступности сервера"""
        try:
            response = requests.get(f"{self.base_url}/token/", timeout=2)
            if response.status_code in [200, 405]:
                print(f"{Color.GREEN}✓ Сервер доступен{Color.END}")
                return True
        except:
            pass
        print(f"{Color.RED}✗ Сервер не доступен! Запустите: python manage.py runserver{Color.END}")
        return False

    def print_header(self, text):
        """Вывод заголовка"""
        print(f"\n{Color.HEADER}{Color.BOLD}{'=' * 60}{Color.END}")
        print(f"{Color.HEADER}{Color.BOLD}{text:^60}{Color.END}")
        print(f"{Color.HEADER}{Color.BOLD}{'=' * 60}{Color.END}\n")

    def print_success(self, text):
        """Вывод успешного результата"""
        print(f"{Color.GREEN}✓ {text}{Color.END}")

    def print_error(self, text):
        """Вывод ошибки"""
        print(f"{Color.RED}✗ {text}{Color.END}")

    def print_info(self, text):
        """Вывод информации"""
        print(f"{Color.BLUE}ℹ {text}{Color.END}")

    def print_warning(self, text):
        """Вывод предупреждения"""
        print(f"{Color.YELLOW}⚠ {text}{Color.END}")

    def request(self, method, endpoint, data=None, files=None, token=None, expected_status=None):
        """Выполнение HTTP запроса"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {}

        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=data, timeout=10)
            elif method.upper() == 'POST':
                if files:
                    response = requests.post(url, headers=headers, data=data, files=files, timeout=10)
                else:
                    response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            # Если есть ошибка и код ответа 500, выводим детали
            if response.status_code == 500:
                self.print_error(f"Server Error 500: {url}")
                if response.text:
                    try:
                        error_data = response.json()
                        self.print_error(f"Детали: {json.dumps(error_data, indent=2, ensure_ascii=False)[:300]}")
                    except:
                        self.print_error(f"Текст: {response.text[:300]}")

            return response
        except requests.exceptions.ConnectionError:
            self.print_error(f"Не удалось подключиться к серверу {url}")
            return None
        except requests.exceptions.Timeout:
            self.print_error(f"Таймаут при запросе к {url}")
            return None
        except Exception as e:
            self.print_error(f"Ошибка запроса: {str(e)}")
            return None

    def assert_status(self, response, expected_status, test_name):
        """Проверка статуса ответа"""
        self.results['total'] += 1

        if response is None:
            self.results['failed'] += 1
            self.results['errors'].append(f"{test_name}: Нет ответа от сервера")
            self.print_error(f"{test_name} - Нет ответа")
            return False

        if response.status_code == expected_status:
            self.results['passed'] += 1
            self.print_success(f"{test_name} - {response.status_code}")
            return True
        else:
            self.results['failed'] += 1
            error_msg = f"{test_name} - Ожидался {expected_status}, получен {response.status_code}"
            self.results['errors'].append(error_msg)
            self.print_error(error_msg)
            if response.text:
                try:
                    error_data = response.json()
                    if 'message' in error_data:
                        self.print_error(f"Сообщение: {error_data['message']}")
                    elif 'error' in error_data:
                        self.print_error(f"Ошибка: {error_data['error']}")
                    elif 'detail' in error_data:
                        self.print_error(f"Детали: {error_data['detail']}")
                    else:
                        self.print_error(f"Ответ: {json.dumps(error_data, indent=2, ensure_ascii=False)[:200]}")
                except:
                    self.print_error(f"Ответ: {response.text[:200]}")
            return False

    def get_token(self, username, password):
        """Получение JWT токена"""
        response = self.request('POST', 'token/', data={
            'username': username,
            'password': password
        })

        if response and response.status_code == 200:
            data = response.json()
            self.token = data.get('access')
            self.refresh_token = data.get('refresh')
            self.print_success(f"Получен токен для {username}")
            return self.token
        else:
            if response:
                self.print_error(f"Не удалось получить токен для {username}: {response.status_code}")
                if response.text:
                    try:
                        error_data = response.json()
                        self.print_error(f"Ошибка: {error_data.get('detail', response.text[:100])}")
                    except:
                        self.print_error(f"Ответ: {response.text[:100]}")
            else:
                self.print_error(f"Не удалось получить токен для {username}: нет ответа")
            return None


class TestDataCreator:
    """Создание тестовых данных в БД"""

    @staticmethod
    def create_users():
        """Создание тестовых пользователей"""
        print(f"\n{Color.BLUE}Создание тестовых пользователей...{Color.END}")

        users_data = [
            {'username': 'admin', 'password': 'Admin123!', 'role': 'Admin',
             'first_name': 'Админ', 'last_name': 'Администраторов', 'email': 'admin@test.com'},
            {'username': 'manager', 'password': 'Manager123!', 'role': 'Manager',
             'first_name': 'Менеджер', 'last_name': 'Менеджеров', 'email': 'manager@test.com'},
            {'username': 'security', 'password': 'Security123!', 'role': 'Security',
             'first_name': 'Охранник', 'last_name': 'Охранов', 'email': 'security@test.com'},
            {'username': 'contractor_user', 'password': 'Contractor123!', 'role': 'Contractor',
             'first_name': 'Подрядчик', 'last_name': 'Подрядчиков', 'email': 'contractor@test.com'},
        ]

        created_users = {}
        for data in users_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'role': data['role'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'email': data['email'],
                    'is_active': True,
                    'is_staff': data['role'] == 'Admin',
                    'is_superuser': data['role'] == 'Admin',
                }
            )
            # Всегда обновляем пароль
            user.set_password(data['password'])
            user.save()

            if created:
                print(f"  ✓ Создан пользователь: {user.username} ({user.role})")
            else:
                print(f"  ℹ Обновлен пользователь: {user.username} ({user.role})")

            created_users[data['username']] = user

        return created_users

    @staticmethod
    def create_contractors():
        """Создание тестовых подрядчиков"""
        print(f"\n{Color.BLUE}Создание тестовых подрядчиков...{Color.END}")

        contractors_data = [
            {'inn': '123456789012', 'name': 'ООО СтройТех', 'status_accreditation': 'Accreditate'},
            {'inn': '987654321098', 'name': 'ООО МонтажСервис', 'status_accreditation': 'Noaccreditate'},
            {'inn': '456789123456', 'name': 'ИП Иванов', 'status_accreditation': 'Noaccreditate'},
            {'inn': '111222333444', 'name': 'ООО ТестТех', 'status_accreditation': 'Noaccreditate'},
        ]

        created_contractors = {}
        for data in contractors_data:
            contractor, created = Contractor.objects.get_or_create(
                inn=data['inn'],
                defaults={
                    'name': data['name'],
                    'status_accreditation': data['status_accreditation']
                }
            )
            if created:
                print(f"  ✓ Создан подрядчик: {contractor.name} (ИНН: {contractor.inn})")
            else:
                print(f"  ℹ Подрядчик уже существует: {contractor.name}")

            created_contractors[contractor.inn] = contractor

        return created_contractors

    @staticmethod
    def create_documents(contractors):
        """Создание тестовых документов"""
        print(f"\n{Color.BLUE}Создание тестовых документов...{Color.END}")

        today = datetime.now().date()

        docs_data = []

        # Для ООО СтройТех - аккредитован
        if '123456789012' in contractors:
            contractor = contractors['123456789012']
            docs_data.extend([
                {
                    'contractor': contractor,
                    'type': 'Insurance',
                    'release_date': today - timedelta(days=365),
                    'expiration_date': today + timedelta(days=365),
                },
                {
                    'contractor': contractor,
                    'type': 'Registry',
                    'release_date': today - timedelta(days=365),
                    'expiration_date': today + timedelta(days=365),
                }
            ])

        # Для ООО МонтажСервис - просроченные документы
        if '987654321098' in contractors:
            contractor = contractors['987654321098']
            docs_data.append({
                'contractor': contractor,
                'type': 'Insurance',
                'release_date': today - timedelta(days=730),
                'expiration_date': today - timedelta(days=30),
            })

        created_docs = []
        for data in docs_data:
            doc = ComplianceDocument.objects.create(
                id_contractor=data['contractor'],
                type=data['type'],
                release_date=data['release_date'],
                expiration_date=data['expiration_date'],
            )
            created_docs.append(doc)
            print(f"  ✓ Создан документ: {doc.get_type_display()} для {doc.id_contractor.name}")

        return created_docs

    @staticmethod
    def create_employees(contractors):
        """Создание тестовых сотрудников"""
        print(f"\n{Color.BLUE}Создание тестовых сотрудников...{Color.END}")

        employees_data = []

        if '123456789012' in contractors:
            contractor = contractors['123456789012']
            employees_data.extend([
                {'contractor': contractor, 'first_name': 'Иван', 'last_name': 'Петров',
                 'patronymic': 'Иванович', 'passport': '1234567890'},
                {'contractor': contractor, 'first_name': 'Алексей', 'last_name': 'Сидоров',
                 'patronymic': 'Сергеевич', 'passport': '9876543210'},
                {'contractor': contractor, 'first_name': 'Мария', 'last_name': 'Иванова',
                 'patronymic': 'Петровна', 'passport': '5554443332'},
            ])

        if '987654321098' in contractors:
            contractor = contractors['987654321098']
            employees_data.append(
                {'contractor': contractor, 'first_name': 'Сергей', 'last_name': 'Смирнов',
                 'patronymic': 'Александрович', 'passport': '1112223334'}
            )

        created_employees = []
        for data in employees_data:
            employee, created = ContractorEmployee.objects.get_or_create(
                id_contractor=data['contractor'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                patronymic=data['patronymic'],
                defaults={'passport': data['passport']}
            )
            if created:
                created_employees.append(employee)
                print(f"  ✓ Создан сотрудник: {employee.last_name} {employee.first_name}")
            else:
                print(f"  ℹ Сотрудник уже существует: {employee.last_name} {employee.first_name}")

        return created_employees

    @staticmethod
    def create_passes(employees):
        """Создание тестовых пропусков"""
        print(f"\n{Color.BLUE}Создание тестовых пропусков...{Color.END}")

        if not employees:
            print(f"  {Color.YELLOW}⚠ Нет сотрудников для создания пропусков{Color.END}")
            return []

        passes_data = []

        # Для первого сотрудника - постоянный пропуск
        if len(employees) > 0:
            passes_data.append({
                'employee': employees[0],
                'type': 'permanent',
                'zona_access': 'Зона А, Зона Б',
                'status': 'active'
            })

        # Для второго сотрудника - временный пропуск
        if len(employees) > 1:
            passes_data.append({
                'employee': employees[1],
                'type': 'temporary',
                'zona_access': 'Зона А',
                'status': 'passive'
            })

        # Для третьего сотрудника - разовый пропуск
        if len(employees) > 2:
            passes_data.append({
                'employee': employees[2],
                'type': 'one_time',
                'zona_access': 'Зона В',
                'status': 'active'
            })

        created_passes = []
        for data in passes_data:
            try:
                pass_obj = AccessPass.objects.create(
                    id_employee=data['employee'],
                    type=data['type'],
                    zona_access=data['zona_access'],
                    status=data['status']
                )
                created_passes.append(pass_obj)
                print(f"  ✓ Создан пропуск: {pass_obj.get_type_display()} для {pass_obj.id_employee.last_name}")
            except Exception as e:
                print(f"  {Color.YELLOW}⚠ Не удалось создать пропуск: {str(e)}{Color.END}")

        return created_passes

    @staticmethod
    def create_blacklist(users, contractors, employees):
        """Создание тестовых записей в черном списке"""
        print(f"\n{Color.BLUE}Создание тестовых записей в черном списке...{Color.END}")

        blacklist_data = []

        # Добавляем компанию в черный список
        if '456789123456' in contractors:
            contractor = contractors['456789123456']
            blacklist_data.append({
                'entity_type': 'Yurlico',
                'entity_id': str(contractor.id),
                'reason': 'Нарушение правил безопасности',
                'added_by': users.get('admin')
            })

        # Добавляем сотрудника в черный список
        if employees and len(employees) > 2:
            employee = employees[2]
            blacklist_data.append({
                'entity_type': 'Fizlico',
                'entity_id': str(employee.id),
                'reason': 'Попытка проноса запрещенных предметов',
                'added_by': users.get('security')
            })

        created_blacklist = []
        for data in blacklist_data:
            try:
                blacklist_entry = Blacklist.objects.create(
                    entity_type=data['entity_type'],
                    entity_id=data['entity_id'],
                    reason=data['reason'],
                    added_by=data['added_by']
                )
                created_blacklist.append(blacklist_entry)
                print(f"  ✓ Добавлен в черный список: {blacklist_entry.get_entity_type_display()}")
            except Exception as e:
                print(f"  {Color.YELLOW}⚠ Не удалось добавить в черный список: {str(e)}{Color.END}")

        return created_blacklist


class APITestRunner:
    """Запуск тестов API"""

    def __init__(self):
        self.tester = APITester()
        self.test_data = {}

    def print_header(self, text):
        self.tester.print_header(text)

    def setup_test_data(self):
        """Создание тестовых данных"""
        self.print_header("СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ")

        # Создаем пользователей
        users = TestDataCreator.create_users()
        self.test_data['users'] = users

        # Создаем подрядчиков
        contractors = TestDataCreator.create_contractors()
        self.test_data['contractors'] = contractors

        # Создаем документы
        docs = TestDataCreator.create_documents(contractors)
        self.test_data['documents'] = docs

        # Создаем сотрудников
        employees = TestDataCreator.create_employees(contractors)
        self.test_data['employees'] = employees

        # Создаем пропуска
        passes = TestDataCreator.create_passes(employees)
        self.test_data['passes'] = passes

        # Создаем черный список
        blacklist = TestDataCreator.create_blacklist(users, contractors, employees)
        self.test_data['blacklist'] = blacklist

        print(f"\n{Color.GREEN}✓ Тестовые данные созданы{Color.END}")

    def test_auth(self):
        """Тестирование аутентификации"""
        self.print_header("ТЕСТИРОВАНИЕ АУТЕНТИФИКАЦИИ")

        # Получаем токен для Admin
        token = self.tester.get_token('admin', 'Admin123!')
        if token:
            self.tester.assert_status(
                requests.Response() if token else None,
                200,
                "Получение токена Admin"
            )
            self.tester.token = token
        else:
            self.tester.print_error("Не удалось получить токен Admin. Проверьте пользователя.")

    def test_users(self):
        """Тестирование эндпоинтов пользователей"""
        self.print_header("ТЕСТИРОВАНИЕ ПОЛЬЗОВАТЕЛЕЙ")

        if not self.tester.token:
            self.tester.print_error("Нет токена. Пропуск тестов пользователей")
            return

        # GET /users/
        response = self.tester.request('GET', 'users/', token=self.tester.token)
        self.tester.assert_status(response, 200, "GET /users/")

        # GET /users/me/
        response = self.tester.request('GET', 'users/me/', token=self.tester.token)
        self.tester.assert_status(response, 200, "GET /users/me/")

        # POST /users/create/
        response = self.tester.request('POST', 'users/create/', token=self.tester.token, data={
            'username': 'testuser',
            'password': 'Test123!',
            'first_name': 'Тест',
            'last_name': 'Тестов',
            'email': 'test@test.com',
            'role': 'Contractor'
        })
        self.tester.assert_status(response, 201, "POST /users/create/")

        # GET /users/{id}/
        if response and response.status_code == 201:
            user_id = response.json().get('id')
            response = self.tester.request('GET', f'users/{user_id}/', token=self.tester.token)
            self.tester.assert_status(response, 200, f"GET /users/{user_id}/")

    def test_contractors(self):
        """Тестирование эндпоинтов подрядчиков"""
        self.print_header("ТЕСТИРОВАНИЕ ПОДРЯДЧИКОВ")

        if not self.tester.token:
            self.tester.print_error("Нет токена. Пропуск тестов подрядчиков")
            return

        # GET /contractors/
        response = self.tester.request('GET', 'contractors/', token=self.tester.token)
        self.tester.assert_status(response, 200, "GET /contractors/")

        # GET /contractors/ с фильтром
        response = self.tester.request('GET', 'contractors/', token=self.tester.token,
                                       data={'status_accreditation': 'Accreditate'})
        self.tester.assert_status(response, 200, "GET /contractors/ (фильтр по статусу)")

        # GET /contractors/ с поиском
        response = self.tester.request('GET', 'contractors/', token=self.tester.token,
                                       data={'search': 'Строй'})
        self.tester.assert_status(response, 200, "GET /contractors/ (поиск)")

        # POST /contractors/create/
        response = self.tester.request('POST', 'contractors/create/', token=self.tester.token, data={
            'inn': '999888777666',
            'name': 'ООО Тестовый Подрядчик',
            'status_accreditation': 'Noaccreditate'
        })
        self.tester.assert_status(response, 201, "POST /contractors/create/")

        # GET /contractors/{id}/
        if response and response.status_code == 201:
            contractor_id = response.json().get('id')
            if contractor_id:
                response = self.tester.request('GET', f'contractors/{contractor_id}/', token=self.tester.token)
                self.tester.assert_status(response, 200, f"GET /contractors/{contractor_id}/")

                # GET /contractors/{id}/compliance/
                response = self.tester.request('GET', f'contractors/{contractor_id}/compliance/',
                                               token=self.tester.token)
                self.tester.assert_status(response, 200, f"GET /contractors/{contractor_id}/compliance/")

    def test_documents(self):
        """Тестирование эндпоинтов документов"""
        self.print_header("ТЕСТИРОВАНИЕ ДОКУМЕНТОВ")

        if not self.tester.token:
            self.tester.print_error("Нет токена. Пропуск тестов документов")
            return

        # GET /documents/
        response = self.tester.request('GET', 'documents/', token=self.tester.token)
        self.tester.assert_status(response, 200, "GET /documents/")

        # GET /documents/ с фильтром
        response = self.tester.request('GET', 'documents/', token=self.tester.token,
                                       data={'type': 'Insurance'})
        self.tester.assert_status(response, 200, "GET /documents/ (фильтр по типу)")

        # GET /documents/by-contractor/{id}/
        contractor = Contractor.objects.filter(inn='123456789012').first()
        if contractor:
            response = self.tester.request('GET', f'documents/by-contractor/{contractor.id}/', token=self.tester.token)
            self.tester.assert_status(response, 200, f"GET /documents/by-contractor/{contractor.id}/")

    def test_employees(self):
        """Тестирование эндпоинтов сотрудников"""
        self.print_header("ТЕСТИРОВАНИЕ СОТРУДНИКОВ")

        if not self.tester.token:
            self.tester.print_error("Нет токена. Пропуск тестов сотрудников")
            return

        # GET /employees/
        response = self.tester.request('GET', 'employees/', token=self.tester.token)
        self.tester.assert_status(response, 200, "GET /employees/")

        # GET /employees/ с поиском
        response = self.tester.request('GET', 'employees/', token=self.tester.token,
                                       data={'search': 'Петров'})
        self.tester.assert_status(response, 200, "GET /employees/ (поиск)")

        # POST /employees/create/
        contractor = Contractor.objects.filter(inn='123456789012').first()
        if contractor:
            response = self.tester.request('POST', 'employees/create/', token=self.tester.token, data={
                'id_contractor': contractor.id,
                'first_name': 'Николай',
                'last_name': 'Смирнов',
                'patronymic': 'Александрович',
                'passport': '7778889990'
            })
            self.tester.assert_status(response, 201, "POST /employees/create/")

            # GET /employees/by-contractor/{id}/
            response = self.tester.request('GET', f'employees/by-contractor/{contractor.id}/', token=self.tester.token)
            self.tester.assert_status(response, 200, f"GET /employees/by-contractor/{contractor.id}/")

    def test_passes(self):
        """Тестирование эндпоинтов пропусков"""
        self.print_header("ТЕСТИРОВАНИЕ ПРОПУСКОВ")

        if not self.tester.token:
            self.tester.print_error("Нет токена. Пропуск тестов пропусков")
            return

        # GET /passes/
        response = self.tester.request('GET', 'passes/', token=self.tester.token)
        self.tester.assert_status(response, 200, "GET /passes/")

        # GET /passes/ с фильтром
        response = self.tester.request('GET', 'passes/', token=self.tester.token,
                                       data={'status': 'active'})
        self.tester.assert_status(response, 200, "GET /passes/ (фильтр по статусу)")

        # POST /passes/create/
        employee = ContractorEmployee.objects.filter(last_name='Петров').first()
        if employee:
            response = self.tester.request('POST', 'passes/create/', token=self.tester.token, data={
                'id_employee': employee.id,
                'type': 'permanent',
                'zona_access': 'Тестовая зона',
                'status': 'active'
            })
            self.tester.assert_status(response, 201, "POST /passes/create/")

            if response and response.status_code == 201:
                # GET /passes/check/
                response = self.tester.request('GET', 'passes/check/', token=self.tester.token,
                                               data={'employee_id': employee.id})
                self.tester.assert_status(response, 200, f"GET /passes/check/ (employee_id={employee.id})")

                # GET /passes/by-employee/{id}/
                response = self.tester.request('GET', f'passes/by-employee/{employee.id}/', token=self.tester.token)
                self.tester.assert_status(response, 200, f"GET /passes/by-employee/{employee.id}/")

    def test_blacklist(self):
        """Тестирование эндпоинтов черного списка"""
        self.print_header("ТЕСТИРОВАНИЕ ЧЕРНОГО СПИСКА")

        if not self.tester.token:
            self.tester.print_error("Нет токена. Пропуск тестов черного списка")
            return

        # GET /blacklist/
        response = self.tester.request('GET', 'blacklist/', token=self.tester.token)
        self.tester.assert_status(response, 200, "GET /blacklist/")

        # GET /blacklist/check/
        contractor = Contractor.objects.filter(inn='456789123456').first()
        if contractor:
            response = self.tester.request('GET', 'blacklist/check/', token=self.tester.token,
                                           data={'entity_type': 'Yurlico', 'entity_id': contractor.id})
            self.tester.assert_status(response, 200, f"GET /blacklist/check/ (Yurlico/{contractor.id})")

    def test_permissions(self):
        """Тестирование прав доступа для разных ролей"""
        self.print_header("ТЕСТИРОВАНИЕ ПРАВ ДОСТУПА")

        roles = {
            'manager': ('Manager123!', 200),  # Менеджер имеет доступ
            'security': ('Security123!', 200),  # Охрана имеет доступ к подрядчикам
            'contractor_user': ('Contractor123!', 200),  # Подрядчик имеет доступ к подрядчикам
        }

        for username, (password, expected_status) in roles.items():
            print(f"\n{Color.BLUE}Тестирование роли: {username}{Color.END}")

            token = self.tester.get_token(username, password)
            if not token:
                self.tester.print_warning(f"Не удалось получить токен для {username}")
                continue

            # Попытка получить список подрядчиков (доступно всем аутентифицированным)
            response = self.tester.request('GET', 'contractors/', token=token)
            # Ожидаем 200 для всех аутентифицированных
            self.tester.assert_status(response, expected_status, f"{username} -> GET /contractors/")

    def print_results(self):
        """Вывод результатов тестирования"""
        self.print_header("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")

        total = self.tester.results['total']
        passed = self.tester.results['passed']
        failed = self.tester.results['failed']

        print(f"Всего тестов: {total}")
        print(f"{Color.GREEN}Успешно: {passed}{Color.END}")
        print(f"{Color.RED}Провалено: {failed}{Color.END}")

        if failed > 0:
            print(f"\n{Color.RED}Ошибки:{Color.END}")
            for error in self.tester.results['errors']:
                print(f"  {Color.RED}✗ {error}{Color.END}")

        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\n{Color.BOLD}Успешность: {success_rate:.1f}%{Color.END}")

        if failed == 0:
            print(f"\n{Color.GREEN}{Color.BOLD}🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!{Color.END}")
        else:
            print(f"\n{Color.YELLOW}⚠ Есть проваленные тесты. Проверьте ошибки выше.{Color.END}")

    def run(self):
        """Запуск всех тестов"""
        print(f"\n{Color.HEADER}{Color.BOLD}")
        print("=" * 60)
        print("ЗАПУСК ТЕСТИРОВАНИЯ API".center(60))
        print("=" * 60)
        print(f"{Color.END}\n")

        # Создаем тестовые данные
        self.setup_test_data()

        # Запускаем тесты
        self.test_auth()
        self.test_users()
        self.test_contractors()
        self.test_documents()
        self.test_employees()
        self.test_passes()
        self.test_blacklist()
        self.test_permissions()

        # Выводим результаты
        self.print_results()


def main():
    """Главная функция"""
    runner = APITestRunner()
    runner.run()


if __name__ == '__main__':
    main()