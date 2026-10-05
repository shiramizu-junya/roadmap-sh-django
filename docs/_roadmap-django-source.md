# roadmap.sh/django 単元素材

出典: https://github.com/kamranahmedse/developer-roadmap
取得日: 2026-10-06

> 各トピックの本文は短い。教材化の素材ではなく、
> 「扱う範囲」の定義として使う（_prompt.md §2.6）。
> SSR 系（テンプレート / フォーム / CBV）は意図的な範囲外。

---

## admin-customization@KHoau3Pz7o951L8Ivryk0

# Admin Customization

Admin customization in Django refers to modifying the default appearance and functionality of the Django admin interface. This involves tailoring the admin site to better suit the specific needs of a project, such as changing the display of fields, adding custom actions, or altering the overall layout. Customization allows developers to create a more user-friendly and efficient experience for content managers and administrators.

Visit the following resources to learn more:

- [@official@The Django admin site](https://docs.djangoproject.com/en/6.0/ref/contrib/admin/#custom-template-options)
- [@article@Customizing the Django Admin](https://testdriven.io/blog/customize-django-admin/)
- [@article@Customizing the Django Admin](https://earthly.dev/blog/customize-django-admin-site/)
- [@video@Learn Django - Admin](https://www.youtube.com/watch?v=c_S0ZQs81XQ&list=PLOLrQ9Pn6cazhaxNDhcOIPYXt2zZhAXKO)
## adminpy@tffzsnhXGpN8-CPLgmdxn

# Django's admin.py

`admin.py` is a Python file within a Django app that's responsible for configuring how your models are displayed and managed in Django's automatically generated admin interface. It allows you to register your models, customize their appearance, add search functionality, and define how they can be edited through the admin site. This file essentially bridges the gap between your data models and the user-friendly admin panel.

Visit the following resources to learn more:

- [@official@django-admin and manage.py](https://docs.djangoproject.com/en/6.0/ref/django-admin/)
- [@article@Django Admin](https://www.w3schools.com/django/django_admin.php)
## aggregations@9PRY8NUilH2xITVyhpQSy

# Aggregations

Aggregations in Django allow you to summarize data from multiple objects in your database. They compute a single summary value (like average, sum, or count) for a group of objects. Unlike annotations, which add a field to each object in a queryset, aggregations return a single value for the entire queryset. So, annotations add extra data to each item, while aggregations give you a summary of the whole collection.

Visit the following resources to learn more:

- [@official@Aggregation](https://docs.djangoproject.com/en/6.0/topics/db/aggregation/)
- [@article@QuerySets and aggregations in Django](https://blog.logrocket.com/querysets-and-aggregations-in-django/)
- [@article@Django Annotate and aggregate explained](https://coffeebytes.dev/en/django/django-annotate-and-aggregate-explained/)
- [@video@Django Aggregation & Annotation / values() and values_list() functions](https://www.youtube.com/watch?v=LEsmHKZLsBI)
## asynchronous-django@8AuyffbXskd8jltqyJVer

# Asynchronous Django

Asynchronous programming allows a program to execute multiple tasks seemingly at the same time without waiting for each task to complete before starting the next. Instead of blocking and waiting, the program can switch between tasks as needed, improving efficiency. In Django, this is achieved using tools like `async` and `await` keywords in Python, along with asynchronous views and middleware, enabling the application to handle more requests concurrently and reduce response times, especially for tasks involving I/O operations like database queries or external API calls.

Visit the following resources to learn more:

- [@official@Asynchronous support](https://docs.djangoproject.com/en/6.0/topics/async/)
- [@article@Unlocking Performance: A Guide to Async Support in Django](https://dev.to/pragativerma18/unlocking-performance-a-guide-to-async-support-in-django-2jdj)
- [@article@Running tasks concurrently in Django asynchronous views](https://fly.io/django-beats/running-tasks-concurrently-in-django-asynchronous-views/)
- [@video@Introduction to async views in Django | async/await in Django views](https://www.youtube.com/watch?v=YneIutRhmgo)
## authentication@k2P3gilbLJ7tjbLhBym_m

# Authentication

Authentication is the process of verifying the identity of a user, device, or other entity attempting to access a system or resource. It confirms that someone or something is who or what they claim to be, typically by checking credentials like usernames and passwords against a stored database. Successful authentication grants access, while failure denies it.

Visit the following resources to learn more:

- [@official@User authentication in Django](https://docs.djangoproject.com/en/6.0/topics/auth/)
- [@article@Django Tutorial Part 8: User authentication and permissions](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/Django/Authentication)
- [@article@Django Authentication Made Easy: A Complete Guide to Registration, Login, and User Management](https://dev.to/ebereplenty/django-authentication-made-easy-a-complete-guide-to-registration-login-and-user-management-2jih)
- [@video@Login With User Authentication - Django Wednesdays #21](https://www.youtube.com/watch?v=CTrVDi3tt8o)
## authorization@8-LeguN1r6pLVGvBbwzPZ

# Authorization

Authorization is the process of determining whether a user has permission to access a specific resource or perform a particular action. It focuses on verifying what an authenticated user is allowed to do within a system, ensuring that they only have access to the resources and functionalities they are entitled to. This is distinct from authentication, which confirms the user's identity.

Visit the following resources to learn more:

- [@official@Permissions and Authorization¶](https://docs.djangoproject.com/en/6.0/topics/auth/default/#topic-authorization)
- [@article@Django Tutorial Part 8: User authentication and permissions](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/Django/Authentication)
- [@video@Python Django User Authorization tutorial](https://www.youtube.com/watch?v=4Ba8AtSwJwg)
## background-tasks@x19j7d1jd_uFhy85w71i0

# Background Tasks

Background tasks in Django are processes that run independently of the main web application, without blocking user requests. They are useful for handling time-consuming or resource-intensive operations like sending emails, processing large datasets, or generating reports. By offloading these tasks to the background, the web application remains responsive and provides a better user experience.

Visit the following resources to learn more:

- [@official@Django’s Tasks framework](https://docs.djangoproject.com/en/6.0/topics/tasks/)
- [@video@Background tasks in Django | How to create tasks in the background in Django - Quick & easy](https://www.youtube.com/watch?v=PUT29lvDFco)
- [@video@Intro to Background Tasks in Django With Celery](https://www.youtube.com/watch?v=y6FG-kKhGwA)
## built-in-user-model@SEEiAOOxLGUaZi3wYncUm

# Built-in User Model

Django provides a default user model that handles common authentication tasks like user registration, login, and permission management. This model includes fields like username, password, email, first name, and last name, and it offers methods for password hashing and user authorization. It serves as a foundation for managing users in your Django project, and can be customized or extended to fit specific application requirements.

Visit the following resources to learn more:

- [@official@User model](https://docs.djangoproject.com/en/6.0/ref/contrib/auth/)
- [@article@How to Get the User Model in Django – A Simple Guide With Examples](https://www.freecodecamp.org/news/how-to-get-user-model-in-django/)
- [@article@User Models](https://d-libro.com/topic/user-models/)
## caching@UDpTybashBHcy2S-oooww

# Caching

Caching is a technique to store frequently accessed data in a temporary storage location (the cache) to speed up retrieval in the future. When data is requested, the system first checks the cache. If the data is present (a "cache hit"), it's served directly from the cache, avoiding the slower process of fetching it from the original source (like a database). If the data isn't in the cache (a "cache miss"), it's retrieved from the original source, stored in the cache, and then served to the user. This reduces latency and improves application performance.

Visit the following resources to learn more:

- [@official@Django’s cache framework](https://docs.djangoproject.com/en/6.0/topics/cache/)
- [@article@Django Caching 101: Understanding the Basics and Beyond](https://dev.to/pragativerma18/django-caching-101-understanding-the-basics-and-beyond-49p)
- [@article@Django Cache Examples with a Complete Project](https://medium.com/django-unleashed/django-cache-examples-with-a-complete-project-7307322756e2)
- [@video@Caching with Redis and Django!](https://www.youtube.com/watch?v=5W2Yff00H8s)
## celery@Jjj1dVybPHsdP-57yF7iX

# Celery

Celery is a distributed task queue that allows you to run tasks asynchronously, outside of the typical request-response cycle. It's often used to handle time-consuming or resource-intensive operations, such as sending emails, processing images, or generating reports, without blocking the user's request. This improves the responsiveness and scalability of your web application.

Visit the following resources to learn more:

- [@official@Celery Docs](https://docs.celeryq.dev/en/v5.5.3/index.html)
- [@official@Using Celery with Django](https://docs.celeryq.dev/en/v5.5.3/django/first-steps-with-django.html)
- [@article@The Definitive Guide to Celery and Django](http://testdriven.io/courses/django-celery/getting-started/)
- [@video@Python Django Celery Introduction](https://www.youtube.com/watch?v=AQYnKn-i0q8&list=PLOLrQ9Pn6cayGytG1fgUPEsUp3Onol8V7)
## class-based-views@49YSIjTsb6Lnv39AukGrD

# Class-Based Views

Class-based views (CBVs) in Django are an alternative way to implement views using Python classes instead of functions. They provide a structured and reusable approach to handling common view logic, promoting code organization and reducing redundancy. CBVs leverage inheritance and mixins to offer a more object-oriented way to define views, making them easier to extend and customize.

Visit the following resources to learn more:

- [@official@Class-based views](https://docs.djangoproject.com/en/6.0/topics/class-based-views/)
- [@article@What Are Django Class-Based Views (CBVs) & its Advantages in 2024](https://www.horilla.com/blogs/what-are-django-class-based-views-cbvs-and-its-advantages/)
- [@video@What are Django class based views & should you use them?](https://www.youtube.com/watch?v=RE0HlKch_3U)
- [@video@Learn Django Class-Based Views - Using TemplateView - theory and examples](https://www.youtube.com/watch?v=GxA2I-n8NR8&list=PLOLrQ9Pn6caxNb9eFZJ6LfY29nZkKmmXT)
## comments@TXhI0IHDH6a4_vNyCDEYH

# Comments in Django Templates

Comments in Django Template Language (DTL) allow developers to embed explanatory notes or temporarily disable sections of template code without affecting the rendered output. These comments are not visible to the end-user in the final HTML. They are useful for documenting the purpose of specific template logic, debugging, or experimenting with different template structures.

Visit the following resources to learn more:

- [@official@comments](https://docs.djangoproject.com/en/6.0/ref/templates/builtins/#comment)
- [@article@Django comment Tag](https://www.w3schools.com/django/django_tags_comment.php)
## create-update-delete@_2hoRFibz8dYBPhHJX8NW

# Create, Update, Delete Operations in Django ORM

The Django ORM (Object-Relational Mapper) provides a high-level interface for interacting with databases. It allows you to perform CRUD (Create, Read, Update, Delete) operations on your database tables using Python code instead of writing raw SQL queries. This simplifies database interactions and makes your code more maintainable.

Visit the following resources to learn more:

- [@official@Making Queries](https://docs.djangoproject.com/en/6.0/topics/db/queries/#retrieving-objects)
- [@article@Django Insert Data](https://www.w3schools.com/django/django_insert_data.php)
- [@article@Django Update Data](https://www.w3schools.com/django/django_update_data.php)
- [@article@Django Delete Data](https://www.w3schools.com/django/django_delete_data.php)
## createview@osfekQvv2IjQir8xG7Jqn

# CreateView

`CreateView` is a powerful generic class-based view in Django that simplifies the process of creating new objects in your database. It handles displaying a form for creating the object, validating the submitted data, and saving the new object to the database if the data is valid. It's designed to reduce boilerplate code when you need to create model instances through a web interface.

Visit the following resources to learn more:

- [@official@CreateView](https://docs.djangoproject.com/en/6.0/ref/class-based-views/generic-editing/#django.views.generic.edit.CreateView)
- [@article@Django Class Based Views(CreateView)](https://medium.com/@hellenwain_54279/django-class-based-views-createview-b7c7ead3085)
- [@article@Learn Django Class Based Views - CreateView - Theory and Examples](https://www.youtube.com/watch?v=nW-srV0kKKk)
- [@video@Learn Django Class Based Views - CreateView - Theory and Examples](https://www.youtube.com/watch?v=dOG-aRADaD8)
## csrf@_JaSWTa-VufNB0-6NH5KL

# CSRF

CSRF (Cross-Site Request Forgery) is a web security vulnerability where a malicious website tricks a user's browser into performing actions on a trusted site without the user's knowledge. In Django forms, CSRF protection works by including a unique, secret token in each form. When the form is submitted, Django verifies that this token matches the one stored in the user's session. If they don't match, the request is rejected, preventing the attacker from forging requests.

Visit the following resources to learn more:

- [@official@Cross Site Request Forgery protection](https://docs.djangoproject.com/en/6.0/ref/csrf/)
- [@official@How to use Django’s CSRF protection](https://docs.djangoproject.com/en/6.0/howto/csrf/)
- [@video@What Is CSRF Token In Django and Why Is It Used?](https://www.youtube.com/watch?v=iJmezMBJqEs)
- [@video@Django - AJAX Requests, HTMX & CSRF Tokens](https://www.youtube.com/watch?v=lc1sOvRaFpg)
## custom-fields@7dV6o6DnKkv6TX7KCbnzC

# Custom Fields

Custom fields in Django allow you to define your own field types beyond the standard ones provided by Django, such as CharField, IntegerField, and DateTimeField. This is useful when you need to store data in a specific format or require specialized validation logic that isn't covered by the built-in field types. By creating custom fields, you can seamlessly integrate your unique data requirements into your Django models.

Visit the following resources to learn more:

- [@official@How to create custom model fields](https://docs.djangoproject.com/en/6.0/howto/custom-model-fields/)
- [@article@Django: using custom classes for model fields](https://medium.com/@luccascorrea/django-using-custom-classes-for-model-fields-38e58914ba5c)
- [@article@How to Create Custom Model Fields in Django \[2024\]](https://www.horilla.com/blogs/how-to-create-custom-model-fields-in-django/)
- [@video@Django ORM - Creating a Custom field Subclass](https://www.youtube.com/watch?v=b10NxZ7JEjE)
## custom-user-model@F0OPk3bIoeXhIRthKg9MD

# Custom User Model

A custom user model in Django allows developers to define their own user model instead of using the default Django user model. This provides flexibility to include additional fields or methods tailored to the specific requirements of an application, such as storing extra profile information or implementing custom authentication logic. By creating a custom user model, you gain full control over the user representation within your Django project.

Visit the following resources to learn more:

- [@official@Customizing authentication in Django¶](https://docs.djangoproject.com/en/6.0/topics/auth/customizing/)
- [@article@Creating a Custom User Model in Django](https://testdriven.io/blog/django-custom-user-model/)
- [@video@Learn Django - Build a Custom User Model with Extended Fields](https://www.youtube.com/watch?v=Ae7nc1EGv-A)
## customization@oCxrIu2UfV6loYn8ncaLu

# Custom Middleware

Middleware in Django is a framework of hooks into Django's request/response processing. It's a way to modify the incoming request or outgoing response at various points in the process. Customization allows developers to create their own middleware components to handle specific tasks, such as request logging, authentication checks, or modifying response headers, tailoring the framework to their application's unique needs.

Visit the following resources to learn more:

- [@article@Understanding Django Middleware: How to Create Custom Middleware](https://medium.com/@farad.dev/understanding-django-middleware-how-to-create-custom-middleware-789744722df3)
- [@video@Django Custom Middleware - Tutorial With Examples](https://www.youtube.com/watch?v=ELOgWKQpxB8)
- [@video@Writing Django Middleware (with tests!) | HTMX middleware | IP Blacklist middleware](https://www.youtube.com/watch?v=--ddZc39wVQ)
## customizing-views@eQaN3y7cQgOcQ1BstNV-4

# Customizing Views

Customizing views in Django involves modifying the default behavior of view functions or classes to suit specific application needs. This can include adding extra context data, altering the template used for rendering, or overriding methods in class-based views to change how they handle requests and responses. Customization allows developers to tailor the view logic to precisely match the requirements of different features and functionalities within a Django project.

Visit the following resources to learn more:

- [@official@View decorators](https://docs.djangoproject.com/en/6.0/topics/http/decorators/)
- [@article@An Introduction to Django Views](https://blog.jetbrains.com/pycharm/2025/01/django-views/)
- [@article@Customising Django’s Class-based view.](https://medium.com/@krystianmaccs_66962/customising-djangos-class-based-view-e2ed0312a037)
- [@video@How to Create Custom Views in Python Django | Step-by-Step Tutorial](https://www.youtube.com/watch?v=ZigbVn5gKZA)
## debug_toolbar@OSkwgXDOhm6oyk_VlUbUc

# Django Debug Toolbar

The Django Debug Toolbar is a powerful set of panels that display various debugging information about the current request and response. It appears as a collapsible toolbar in your browser when you're developing a Django application. This toolbar provides insights into database queries, template rendering, settings, headers, static files, and more, helping developers identify and resolve performance bottlenecks and other issues quickly.

Visit the following resources to learn more:

- [@official@Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/en/latest/)
- [@opensource@debug_toolbar](https://github.com/django-commons/django-debug-toolbar)
- [@article@Django Debug Toolbar: Configuration and Overview](https://medium.com/@hmbarotov/django-debug-toolbar-configuration-and-overview-97dbe8279279)
- [@video@Django Debug Toolbar - A Tool to Help You With Your Django Projects](https://www.youtube.com/watch?v=H-vLUoXKKIs)
## debugging@x45F-FdQOch35hZqNMfIn

# Debugging

Debugging in Django involves identifying and fixing errors in your code. When your Django application isn't working as expected, debugging helps you understand why. This process typically involves using tools and techniques to inspect your code's behavior, examine variables, and trace the flow of execution to pinpoint the source of the problem and resolve it.

Visit the following resources to learn more:

- [@official@DEBUG Mode](https://docs.djangoproject.com/en/6.0/ref/settings/#std-setting-DEBUG)
- [@article@Writing your first Django app, part 8¶](https://docs.djangoproject.com/en/6.0/intro/tutorial08/)
- [@article@Mastering Django debugging: a complete guide](https://www.aubergine.co/insights/mastering-django-debugging-a-complete-guide)
- [@video@How To Debug a Django Application in VS CODE (Visual Studio Code)](https://www.youtube.com/watch?v=spmFjhQIKOo)
## deleteview@RpvuHOwFN03aeY3hvt1N0

# DeleteView

`DeleteView` in Django is a pre-built class-based view designed to handle the deletion of a specific object from your database. It provides a structured way to present a confirmation page to the user, process the deletion upon confirmation, and then redirect the user to another page. This simplifies the process of creating views that handle object deletion, reducing boilerplate code.

Visit the following resources to learn more:

- [@official@DeleteView](https://docs.djangoproject.com/en/6.0/ref/class-based-views/generic-editing/#django.views.generic.edit.DeleteView)
- [@article@Django DeleteView](https://www.pythontutorial.net/django-tutorial/django-deleteview/)
- [@article@Try DJANGO Tutorial - 39 - Class Based Views - DeleteView](https://www.youtube.com/watch?v=a718ii0Lf6M)
## deployment@jnR93iiFLqqpahhqq4w8-

# Deployment

Deployment is the process of making your Django project accessible to users on the internet. This involves transferring your code, database, and other assets to a server, configuring the server to run your application, and ensuring that it can handle incoming requests. It's the final step in the development lifecycle, allowing users to interact with your Django application.

Visit the following resources to learn more:

- [@official@How to deploy Django](https://docs.djangoproject.com/en/6.0/howto/deployment/)
- [@article@Django Tutorial Part 11: Deploying Django to production](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/Django/Deployment)
- [@video@Python Django Tutorial: Deploying Your Application (Option #1) - Deploy to a Linux Server](https://www.youtube.com/watch?v=Sa_kQheCnds)
- [@video@The 4 best ways to deploy a Django application](https://www.youtube.com/watch?v=IoxHUrbiqUo)
## detailview@D8vZfjzzt3gPda-6iF5Y4

# DetailView

DetailView is a pre-built class-based view in Django that simplifies the process of displaying the details of a single object. It automatically fetches an object from the database based on a provided lookup (typically a primary key or slug) and renders it using a specified template. This eliminates the need to write repetitive code for common detail view scenarios.

Visit the following resources to learn more:

- [@official@DetailView](https://docs.djangoproject.com/en/6.0/ref/class-based-views/generic-display/#detailview)
- [@article@Django DetailView](https://www.pythontutorial.net/django-tutorial/django-detailview/)
- [@article@Django Tutorial Part 6: Generic list and detail views](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/Django/Generic_views)
- [@video@Django 2 for Beginners #23 DetailView](https://www.youtube.com/watch?v=IkqsW8slOO0)
## django_silk@i8me37ZwzObjy1-JbrRjf

# django-silk

django-silk is a powerful profiling and inspection tool designed for the Django framework. It intercepts and stores HTTP requests and database query data, providing a real-time view of your application's performance. This allows developers to pinpoint bottlenecks and optimize code for improved efficiency.

Visit the following resources to learn more:

- [@official@Django Silk Docs](https://silk.readthedocs.io/en/latest/)
- [@opensource@django-silk](https://github.com/jazzband/django-silk)
- [@article@Profiling Django application using django-silk.](https://medium.com/@sharif-42/profiling-django-application-using-django-silk-62cdea83fb83)
- [@video@django-silk for Profiling and Optimization with Django REST Framework](https://www.youtube.com/watch?v=OG8alXR4bEs)
## django--rest-framework@ultPpF8Lpqry-SdAbNCB1

# Django REST Framework

Django REST Framework is a powerful and flexible toolkit for building Web APIs. It provides a set of tools and libraries that simplify the process of creating RESTful APIs with Django, handling tasks like request parsing, serialization, authentication, and permissioning. It allows developers to easily expose Django models and data through well-defined API endpoints.

Visit the following resources to learn more:

- [@official@Django REST framework](https://www.django-rest-framework.org/)
- [@opensource@django-rest-framework](https://github.com/encode/django-rest-framework)
- [@article@Django REST Framework Basics](https://testdriven.io/blog/drf-basics/)
- [@video@Django REST Framework - API Development with Django](https://www.youtube.com/playlist?list=PL-2EBeDYMIbTLulc9FSoAXhbmXpLq2l5t)
## django-admin@Voo8COgeTLD-607m793gh

# Django Admin

Django Admin is a built-in interface in Django that allows you to easily manage your application's data. It provides a user-friendly way to create, read, update, and delete (CRUD) records in your database tables through an automatically generated web interface, based on your models. This eliminates the need to build custom admin panels from scratch.

Visit the following resources to learn more:

- [@official@The Django admin site](https://docs.djangoproject.com/en/6.0/ref/contrib/admin/)
- [@official@django-admin and manage.py](https://docs.djangoproject.com/en/6.0/ref/django-admin/)
- [@article@Django Tutorial Part 4: Django admin site](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/Django/Admin_site)
- [@video@Learn Django - Admin](https://www.youtube.com/playlist?list=PLOLrQ9Pn6cazhaxNDhcOIPYXt2zZhAXKO)
## django-allauth@YKyWtsxm1HcVsA56iyEOJ

# Django-allauth

Django-allauth is a reusable Django app that provides comprehensive social authentication, registration, account management, as well as local username/password authentication. It simplifies the process of integrating various authentication providers (like Google, Facebook, Twitter, etc.) into your Django project, handling the complexities of OAuth and other authentication protocols. It also offers features like email verification, password reset, and account linking.

Visit the following resources to learn more:

- [@official@django-allauth](https://allauth.org/)
- [@official@django-allauth Docs](https://docs.allauth.org/en/latest/)
- [@article@Django-allauth Tutorial](https://learndjango.com/tutorials/django-allauth-tutorial)
- [@video@django-allauth - Deep Dive!](https://www.youtube.com/watch?v=nmj7ThneEnc&list=PL-2EBeDYMIbQqZZoo5Dj8YAkPnZeJfcZS)
## django-forms@jhMYTiVacTLeatfAjAnPJ

# Django Forms Validation

Form validation in Django involves verifying that the data submitted by a user through a form meets specific requirements before it's processed and saved. This ensures data integrity and prevents errors by checking for things like required fields, correct data types, valid ranges, and unique values. Django provides built-in tools and mechanisms to define and execute these validation rules, making it easier to create robust and reliable forms.

Visit the following resources to learn more:

- [@official@Working with forms](https://docs.djangoproject.com/en/6.0/topics/forms/)
- [@article@Django Tutorial Part 9: Working with forms](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/Django/Forms#overview)
- [@video@Python Django Forms tutorial](https://www.youtube.com/watch?v=GQKKjrdS6pc)
- [@video@Django Forms Full Course](https://www.youtube.com/watch?v=pLMH_wzyTjk&list=PLaUQIPIyD0z43DiRKM0x8YNEB-1QNCOwR)
## django-ninja@B86paKhwiZsM5XP-V-AE8

# Django Ninja

Django Ninja is a web framework for building APIs with Django and Python 3.7+ with type hints. It focuses on providing a fast and efficient way to create REST APIs using standard Python type annotations for request validation, serialization, and documentation generation. It simplifies API development by automating many of the common tasks, such as input validation and output serialization, while also providing automatic OpenAPI schema generation.

Visit the following resources to learn more:

- [@official@First Steps](https://django-ninja.dev/tutorial/)
- [@opensource@django-ninja](https://github.com/vitalik/django-ninja)
- [@video@Django-Ninja APIs - Modern API Development in Django](https://www.youtube.com/watch?v=XqkqbsdtoMI)
- [@video@Django Ninja - The new DRF killer?! 🥷](https://www.youtube.com/watch?v=J44FpJ2CYnU)
## django-orm@GQqNJQ3FkO-kBM8WYVBmn

# Django ORM

The Django ORM (Object-Relational Mapper) is a powerful tool that enables developers to interact with databases using Python code, eliminating the need to write raw SQL queries. It acts as an abstraction layer, translating Python objects into database queries and vice versa, simplifying database operations within a Django project. This enables developers to define database schemas using Python classes (models) and perform common database tasks like creating, reading, updating, and deleting data through a high-level API.

Visit the following resources to learn more:

- [@official@Making queries](https://docs.djangoproject.com/en/6.0/topics/db/queries/)
- [@article@An introduction to the Django ORM](https://opensource.com/article/17/11/django-orm)
- [@article@Understanding Django ORM (Object-Relational Mapping)](https://medium.com/django-unleashed/understanding-django-orm-object-relational-mapping-16f3c29db7d7)
- [@video@Django ORM Deep Dive](https://www.youtube.com/watch?v=EsBqIZmR2Uc&list=PL-2EBeDYMIbQXKsyNweppuFptuogJe2L-)
## django-shell@R4-oE2zFnwxvF05u5DYV4

# Django Shell

The Django Shell is an interactive Python interpreter that provides direct access to your Django project's models, database, and settings. It allows you to test code snippets, query data, and perform administrative tasks without needing to run your entire application. It's essentially a command-line environment pre-configured with your Django project's settings and models.

Visit the following resources to learn more:

- [@official@django-admin and manage.py](https://docs.djangoproject.com/en/6.0/ref/django-admin/)
- [@article@Useful Features of the Django Shell](https://www.nickmccullum.com/useful-features-django-shell/)
- [@article@Django Models and Shell](https://medium.com/@ksarthak4ever/django-models-and-shell-8c48963d83a3)
## django-test-framework@HD_-WR69-8f7uhiS0YwYP

# Django Test Framework

The Django test framework provides a structured environment for writing and running tests for Django applications. It includes tools for creating test cases, running tests, and asserting expected outcomes, ensuring that your code functions as intended and remains reliable as your project evolves. It allows developers to write unit tests, integration tests, and other types of tests to verify the correctness of their Django projects.

Visit the following resources to learn more:

- [@official@Testing in Django](https://docs.djangoproject.com/en/6.0/topics/testing/)
- [@official@Writing and running tests](https://docs.djangoproject.com/en/6.0/topics/testing/overview/)
- [@article@Django Tutorial Part 10: Testing a Django web application](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/Django/Testing)
- [@video@Django Testing Tutorial - How To Test Your Django Applications](https://www.youtube.com/watch?v=qwypH3YvMKc&list=PLbpAWbHbi5rMF2j5n6imm0enrSD9eQUaM)
## dtl-syntax@yla_7mhlkfxvI_YZ5Zikm

# DTL Syntax

The Django Template Language (DTL) syntax defines how dynamic content and logic are embedded within HTML templates. It uses tags, variables, and filters to render data from the Django backend into the final HTML output displayed to the user. These elements allow developers to create dynamic web pages by inserting data, performing simple logic, and controlling the structure of the template.

Visit the following resources to learn more:

- [@official@The Django template language](https://docs.djangoproject.com/en/6.0/ref/templates/language/)
- [@article@Django - Template System](https://www.tutorialspoint.com/django/django_template_system.htm)
- [@video@#5 Django tutorials | Django Template Language | DTL](https://www.youtube.com/watch?v=GNlIe5zvBeQ)
## error-pages@mxo_Wwx0To8CaOxBMSQyI

# Error Pages

Error pages in Django are what users see when something goes wrong with your website. Instead of a confusing or blank screen, Django can display informative pages that explain the error. These pages can show technical details helpful for developers during debugging, like the traceback (the sequence of function calls that led to the error) and the values of variables at the time of the error. You can also customize these pages to provide a more user-friendly experience, offering solutions or guidance to users who encounter problems.

Visit the following resources to learn more:

- [@official@Error Views](https://docs.djangoproject.com/en/6.0/ref/views/#error-views)
- [@article@Django 404 (page not found)](https://www.w3schools.com/django/django_404.php)
- [@article@Python Django Handling Custom Error Page](https://medium.com/@yildirimabdrhm/python-django-handling-custom-error-page-807087352bea)
- [@video@Django Full Course - 10.0 - Writing views. Basics, errors, custom error views](https://www.youtube.com/watch?v=4HztW_RlLRo)
## field-options@j4P7KBtfwdGSX0ga0BgpV

# Field Options in Django Models

Field options are attributes you can define within a Django model's field to control its behavior and characteristics. These options allow you to specify constraints, default values, validation rules, and other metadata for each field, influencing how data is stored, displayed, and handled within your application. They provide a way to customize the fields to meet the specific requirements of your data and application logic.

Visit the following resources to learn more:

- [@official@Field options](https://docs.djangoproject.com/en/6.0/topics/db/models/#field-options)
- [@official@Field options](https://docs.djangoproject.com/en/6.0/ref/models/fields/#field-options)
- [@article@Django model fields options](https://swesadiqul.medium.com/django-model-fields-options-8f3651dade6a)
- [@video@Field types and options in Django models](https://www.youtube.com/watch?v=u7MJxv_P2Pk)
## fields-types@CX-9Ii3e9rrokUTF0_hI5

# Model Field Types

Model field types define the kind of data a field in your Django model can hold, such as text, numbers, dates, or relationships to other models. Each field type corresponds to a specific data type in the database and provides built-in validation and form handling. Choosing the right field type is crucial for data integrity and efficient database storage.

Visit the following resources to learn more:

- [@official@Fields](https://docs.djangoproject.com/en/6.0/topics/db/models/#fields)
- [@official@Model field reference](https://docs.djangoproject.com/en/6.0/ref/models/fields/)
- [@article@Django Model Fields – Common Use Cases and How They Work](https://www.freecodecamp.org/news/common-django-model-fields-and-their-use-cases/)
- [@video@Django Full Course - 1.0 - Introduction to models. Fields and field types](https://www.youtube.com/watch?v=1danN1DTzFI)
## filtering--lookups@LDajzTC8AKD-13JVtL0Tk

# Filtering and Lookups in Django ORM

Filtering and lookups are fundamental mechanisms within Django's Object-Relational Mapper (ORM) that allow you to precisely query your database. They enable you to retrieve specific data based on defined criteria, such as finding all users with a particular name or all articles published within a certain date range. These tools provide a powerful and flexible way to interact with your database without writing raw SQL queries.

Visit the following resources to learn more:

- [@official@Field lookups](https://docs.djangoproject.com/en/6.0/topics/db/queries/#field-lookups)
- [@official@How to write custom lookups](https://docs.djangoproject.com/en/6.0/howto/custom-lookups/)
- [@official@filter()](https://docs.djangoproject.com/en/6.0/ref/models/querysets/#django.db.models.query.QuerySet.filter)
- [@video@Django ORM - QuerySet Filtering and Lookups / Ordering and Slicing QuerySets](https://www.youtube.com/watch?v=84BBAGEu064)
## filters--custom-filters@jhZsz4yMcYHgWsigQ4nzU

# Filters & Custom Filters

Filters in Django Template Language (DTL) are used to modify the output of variables. They are applied using a pipe `|` symbol and can perform various transformations like changing case, formatting dates, or truncating text. Custom filters allow developers to define their own reusable template tags to perform specific data manipulations not covered by the built-in filters.

Visit the following resources to learn more:

- [@official@Filters](https://docs.djangoproject.com/en/6.0/ref/templates/language/#filters)
- [@official@Built-in template tags and filters](https://docs.djangoproject.com/en/6.0/ref/templates/builtins/)
- [@article@filter Template Tag](https://www.w3schools.com/django/ref_tags_filter.php)
- [@video@Creating Custom Template Filters in Django!](https://www.youtube.com/watch?v=g2WkvFSVce8)
## filters@jPhWe3MfOLbisxNCaivmz

# Logging Filters

Filters in Django's logging framework provide a way to add extra control over which log records are processed by a handler. They determine whether a specific log record should be emitted based on criteria you define. This allows you to selectively include or exclude log messages based on attributes like the logger name, log level, or any other custom logic you implement. Filters are attached to handlers, and a handler will only process a log record if all of its filters allow it.

Visit the following resources to learn more:

- [@official@Filters](https://docs.djangoproject.com/en/6.0/topics/logging/#topic-logging-parts-filters)
- [@article@Logging in Django — Part II \[Filters and Formatters\]](https://medium.com/django-unleashed/logging-in-django-part-ii-filters-and-formatters-c7190d360ab2)
## fixtures@3CnuISrkDffQgys-x0AP4

# Fixtures

Fixtures in Django provide a way to populate your database with initial data, useful for testing, development, or providing a default dataset for your application. They are typically data files (JSON, XML, or YAML) containing serialized data for one or more database tables, allowing you to easily load and unload data into your Django project's database. This ensures a consistent and repeatable database state.

Visit the following resources to learn more:

- [@official@Fixtures](https://docs.djangoproject.com/en/6.0/topics/db/fixtures/)
- [@official@How to provide initial data for models](https://docs.djangoproject.com/en/6.0/howto/initial-data/)
- [@article@Django Fixtures: A Guide to Managing Static and Test Data](https://www.mindbowser.com/django-fixtures-guide/)
- [@video@Django 4.0: How to Build and Load Fixtures From Scratch](https://www.youtube.com/watch?v=llO8vj6duJc)
## for@Ta2kZmFI4sguQDb1gKJLh

# For Loop in Django Templates

The `for` tag in Django Template Language (DTL) provides a way to iterate over items in a list or other iterable object within your templates. It allows you to display data dynamically by looping through each item and rendering it according to the template's structure. You can access loop-specific variables like the current iteration number and whether it's the first or last item.

Visit the following resources to learn more:

- [@official@for](https://docs.djangoproject.com/en/6.0/ref/templates/builtins/#for)
- [@article@Django for Tag](https://www.w3schools.com/django/django_tags_for.php)
## form-validation@-HGUhMNlPlbwuKMDX1e18

# Form Validation

Form validation in Django is the process of ensuring that the data submitted by a user through a form meets specific requirements before it's saved to the database. This involves checking for things like required fields, correct data types (e.g., email address format), minimum or maximum lengths, and other custom rules you define. If the data doesn't pass these checks, Django provides mechanisms to display error messages to the user, prompting them to correct the input.

Visit the following resources to learn more:

- [@official@Form and field validation](https://docs.djangoproject.com/en/6.0/ref/forms/validation/)
- [@article@Data Validation in Django](https://www.scaler.com/topics/django/data-validation-in-django/)
- [@video@Django ORM - Model Field Validators / Writing Custom Validators / ModelForms](https://www.youtube.com/watch?v=1x0Zdukpjrs)
- [@video@Try DJANGO Tutorial - 27 - Form Validation Methods](https://www.youtube.com/watch?v=wVnQkKf-gHo)
## formatters@rvnqGZxTu3YMH4HQwJ61i

# Formatters

Formatters in Django's logging framework structure log records into human-readable or machine-parseable strings. They define the layout of log messages, specifying which pieces of information (like timestamp, log level, message content, or source file) are included and how they are arranged. You can customize formatters to suit your specific needs, ensuring that log output is clear, consistent, and useful for debugging and monitoring your Django application.

Visit the following resources to learn more:

- [@official@Formatters](https://docs.djangoproject.com/en/6.0/topics/logging/#topic-logging-parts-formatters)
- [@article@Logging in Django — Part II \[Filters and Formatters\]](https://medium.com/django-unleashed/logging-in-django-part-ii-filters-and-formatters-c7190d360ab2)
- [@video@Logging in Django and Python Applications - Handlers / Formatters / Better Stack aggregation](https://www.youtube.com/watch?v=XSwIUnGXrwY)
## function-based-views@3k2Fo1-qldnE38HLtAtvv

# Function-Based Views

Function-based views in Django are Python functions that take a web request and return a web response. They are a simple and direct way to handle HTTP requests and generate the appropriate output, such as HTML, JSON, or redirects. These views provide a basic structure for processing user input, interacting with models, and rendering templates.

Visit the following resources to learn more:

- [@official@Writing views](https://docs.djangoproject.com/en/6.0/topics/http/views/#a-simple-view)
- [@article@Django Functional Based Views](https://medium.com/@rkiptoo5244/django-functional-based-views-37c1d560d154)
- [@article@Class-based vs Function-based Views in Django](https://testdriven.io/blog/django-class-based-vs-function-based-views/)
- [@video@Why I Use Django Function Based Views](https://www.youtube.com/watch?v=mKzStOGIc4A)
## generic-views@-JKD1SRtFWt3b99aPbfx7

# Generic Views

Generic views in Django are pre-built views that handle common web development tasks, like displaying a list of objects, creating new objects, or updating existing ones. They reduce the amount of boilerplate code you need to write by providing reusable logic for interacting with your models and templates. Instead of writing custom view functions for each task, you can configure these generic views to suit your specific needs.

Visit the following resources to learn more:

- [@official@Built-in class-based generic views](https://docs.djangoproject.com/en/6.0/topics/class-based-views/generic-display/)
- [@article@Django Class-Based Views vs Generic Class-Based Views](https://medium.com/@ashishpandey2062/django-class-based-views-vs-generic-class-based-views-2ce548c073db)
- [@article@Class-Based Generic Views in Django](https://thoughtbot.com/blog/class-based-generic-views-in-django)
- [@video@Django - Generic & Class-Based Views! (an alternative to functions)](https://www.youtube.com/watch?v=DDIP-icVpA8)
## handlers@IO9J54i7gSyunGRtIYJra

# Handlers

Handlers in Django's logging framework determine _where_ log messages go. They act as the delivery mechanism, taking log records created by loggers and sending them to specific destinations. These destinations can include the console, files, email addresses, or even external services. Different handlers can be configured to handle different log levels, allowing you to route critical errors to one location and less severe warnings to another.

Visit the following resources to learn more:

- [@official@Handlers](https://docs.djangoproject.com/en/6.0/topics/logging/#topic-logging-parts-handlers)
- [@article@Mastering Logging in Django: A Comprehensive Guide](http://medium.com/@akshatgadodia/mastering-logging-in-django-a-comprehensive-guide-aff850d15ae3)
- [@video@Logging in Django and Python Applications - Handlers / Formatters / Better Stack aggregation](https://www.youtube.com/watch?v=XSwIUnGXrwY)
## how-the-web-works@Xrcl09I9ZShOwhAWynsO6

# How the Web Works

The web operates through a client-server model where a client (like a web browser) sends a request to a server, and the server processes that request and sends back a response. This interaction involves protocols like HTTP for communication, URLs to identify resources, and DNS to translate domain names into IP addresses, enabling users to access and interact with content hosted on servers across the internet.

Visit the following resources to learn more:

- [@article@Introduction to the Internet](https://roadmap.sh/guides/what-is-internet)
- [@article@How does the Internet Work?](https://cs.fyi/guide/how-does-internet-work)
- [@article@How does the Internet work? | MDN Dcos](https://developer.mozilla.org/en-US/docs/Learn_web_development/Howto/Web_mechanics/How_does_the_Internet_work)
- [@video@How the Internet Works in 5 Minutes](https://www.youtube.com/watch?v=7_LPdttKXPc)
## if@9sR_5U94v5qZdEiwngo67

# Conditional Logic in Django Templates

The `if` tag in Django Template Language (DTL) allows you to control which parts of your template are rendered based on the truthiness of a variable or expression. It evaluates a variable, and if that variable is "true" (i.e., exists, is not empty, and is not a false boolean value), the block of code within the `if` tag is rendered. You can also use `elif` and `else` tags to create more complex conditional logic.

Visit the following resources to learn more:

- [@article@if](https://docs.djangoproject.com/en/6.0/ref/templates/builtins/#if)
- [@article@if Template Tag](https://www.w3schools.com/django/ref_tags_if.php)
## installing--django@GB1fgFjrGS-ZM8QTJinOr

# Installing Django

Installing Django involves setting up the Django package on your system so you can start developing web applications. This typically involves using a package installer like pip to download and install the necessary files and dependencies. Once installed, you can verify the installation and begin creating your Django project.

Visit the following resources to learn more:

- [@official@How to install Django](https://docs.djangoproject.com/en/6.0/topics/install/)
- [@official@How to get Django](https://www.djangoproject.com/download/)
- [@article@Django Getting Started](https://www.w3schools.com/django/django_getstarted.php)
- [@video@How To Install Django For Python 3.11.3 | PIP and Django on Windows 10/11 | Django Tutorials](https://www.youtube.com/watch?v=Uq7TkegTXRU)
## introduction@m7fQLURtbiz4BM2UcZPeS

# Introduction

Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design. It takes care of much of the hassle of web development, so you can focus on writing your app without needing to reinvent the wheel. Django follows the model-template-views (MTV) architectural pattern, providing a structured way to build web applications.

Visit the following resources to learn more:

- [@course@Python Django 101](https://www.simplilearn.com/free-python-django-course-skillup)
- [@official@Django Docs](https://docs.djangoproject.com/en/)
- [@article@Django Introduction](https://www.w3schools.com/django/django_intro.php)
- [@video@Django Crash Course – Python Web Framework](https://www.youtube.com/watch?v=0roB7wZMLqI)
## listview@mLMh30_UjacqqNRyKRCiP

# ListView

ListView is a type of generic view in Django that simplifies the process of displaying a list of objects from a database. It automates tasks like fetching data, paginating results, and rendering a template with the list of objects, reducing the amount of boilerplate code you need to write when creating list views.

Visit the following resources to learn more:

- [@official@ListView](https://docs.djangoproject.com/en/6.0/ref/class-based-views/generic-display/)
- [@article@Django Tutorial Part 6: Generic list and detail views](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/Django/Generic_views#overview)
- [@article@Django ListView](https://www.pythontutorial.net/django-tutorial/django-listview/)
- [@video@Django Full Course - 20.1 - Class Based Views. Built-in generic views (ListView, DetailView)](https://www.youtube.com/watch?v=SCvFhXNVVvs)
## localization@waLyhhzu4JkMnhnVdP9xf

# Localization

Localization is the process of adapting a product or content to a specific target market. This involves translating text, but also adapting other elements like date formats, currency symbols, and cultural references to make the product feel native to the user's region. It ensures that the application is accessible and relevant to users from different linguistic and cultural backgrounds.

Visit the following resources to learn more:

- [@official@Internationalization and localization¶](https://docs.djangoproject.com/en/6.0/topics/i18n/)
- [@article@How to Localize Your Django App](https://www.freecodecamp.org/news/localize-django-app/)
- [@article@Django i18n: A beginner's guide](https://lokalise.com/blog/django-i18n-beginners-guide/)
- [@video@Django Internationalization](https://www.youtube.com/watch?v=AlJ8cGbk8ps&list=PLcTpn5-ROA4ysIVpky5IWe0pJbHFvRuYI)
## loggers@zoFHTdr2iBTGdHbmv_9LI

# Loggers

Loggers are the entry points in Django's logging system that your code uses to record events. They capture messages, optionally filter them based on severity levels (like DEBUG, INFO, WARNING, ERROR, and CRITICAL), and then pass them on to handlers. Handlers determine what to do with the log messages, such as writing them to a file, sending them via email, or displaying them on the console. You can configure multiple loggers, each with its own settings, to manage different parts of your application's logging needs.

Visit the following resources to learn more:

- [@official@Loggers](https://docs.djangoproject.com/en/6.0/topics/logging/#loggers)
## logging@SxATl4QiM9iA1_qaUNJXx

# Logging

Logging in Django provides a way to record events that occur while your application is running. It allows you to track errors, warnings, and other important information, which is crucial for debugging and monitoring your application's behavior in different environments. Django's logging system is based on Python's built-in `logging` module, offering flexibility in configuring how and where log messages are stored.

Visit the following resources to learn more:

- [@official@Logging](https://docs.djangoproject.com/en/6.0/topics/logging/)
- [@official@How to configure and use logging¶](https://docs.djangoproject.com/en/6.0/howto/logging/)
- [@article@The Complete Guide to Logging in Django](https://dev.to/pragativerma18/the-complete-guide-to-logging-in-django-5fde)
- [@video@Logging in Django and Python Applications - Handlers / Formatters / Better Stack aggregation](https://www.youtube.com/watch?v=XSwIUnGXrwY)
## managepy@wwKzZhC3xPQ-oymwjW5Yn

# manage.py

`manage.py` is a command-line utility that's automatically created when you start a new Django project. It acts as a central point for running administrative tasks related to your project, such as starting the development server, running tests, creating database migrations, and more. Think of it as a helper script that simplifies interacting with your Django project from the command line.

Visit the following resources to learn more:

- [@article@Writing your first Django app, part 1](https://docs.djangoproject.com/en/6.0/intro/tutorial01/)
- [@article@django-admin and manage.py¶](https://docs.djangoproject.com/en/6.0/ref/django-admin/)
- [@video@Python Basics Tutorial Django Manage.py Startapp](https://www.youtube.com/watch?v=s0Ca-Tdon9Y)
## mariadb@udVG-R6R2UHnvTsXO80xQ

# MariaDB in Django

MariaDB is an open-source relational database management system that is often used as a drop-in replacement for MySQL. It's known for its performance, stability, and rich feature set. Django can be configured to use MariaDB as its database backend, allowing you to store and manage your application's data using this database system.

Visit the following resources to learn more:

- [@official@MariaDB Notes](https://docs.djangoproject.com/en/6.0/ref/databases/#mariadb-notes)
- [@article@Django + MariaDB](https://medium.com/code-zen/django-mariadb-85cc9daeeef8)
- [@video@Django installation with DB (MariaDB/MYSQL) connection & virtualenv](https://www.youtube.com/watch?v=uKSzH4-cG_w)
## media@GA1Zn14Q2EvDmo452V8OO

# Media Folder

The media folder in a Django project is where you store user-uploaded files like images, videos, and documents. Django doesn't automatically create this folder; you typically create it yourself at the project's root or within an app. You'll configure Django to know where this folder is located so it can serve these files correctly.

Visit the following resources to learn more:

- [@article@Working with Static and Media Files in Django](https://testdriven.io/blog/django-static-files/)
## message-framework@AztOoGUtPW_6jP6NqJ5T-

# Message Framework

The message framework in Django provides a way to deliver one-time notification messages, also known as "flash messages," to users. These messages are typically used to provide feedback about the outcome of an action, such as a successful form submission or an error that occurred. They are stored temporarily and displayed to the user on their next page view, then automatically removed.

Visit the following resources to learn more:

- [@official@The messages framework](https://docs.djangoproject.com/en/6.0/ref/contrib/messages/)
- [@article@Messages Framework](https://django-advanced-training.readthedocs.io/en/latest/features/contrib.messages/)
- [@article@Basics of Django Messages Framework](https://micropyramid.com/blog/basics-of-django-message-framework/)
- [@video@#23 Django tutorials | Passing Messages](https://www.youtube.com/watch?v=Mf_97YaUKag)
## middleware@IsZm5SZWJ0CTjxCOKZnn-

# Middleware

Middleware is a framework of hooks into Django's request/response processing. It's a way to modify the incoming request or outgoing response at different stages of the process. Each middleware component is a class that performs a specific function, like modifying request headers, handling sessions, or logging user activity, before the view is executed or after the response is generated.

Visit the following resources to learn more:

- [@official@Middleware](https://docs.djangoproject.com/en/6.0/topics/http/middleware/)
- [@official@Middleware Componetns](https://docs.djangoproject.com/en/6.0/ref/middleware/)
- [@article@What is Django Middleware & Its Role in Request Processing](https://www.horilla.com/blogs/what-is-django-middleware-and-its-role-in-request-processing/)
- [@video@Writing Django Middleware (with tests!) | HTMX middleware | IP Blacklist middleware](https://www.youtube.com/watch?v=--ddZc39wVQ)
## migrations@lUlJdqmd7YRpyRCfgT_EK

# Migrations

Migrations in Django are a way to propagate changes you make to your models (like adding a field, deleting a model, etc.) into your database schema. They are essentially Python files that describe how to alter your database tables to match the current state of your models. Django uses these files to keep your database schema in sync with your application's models over time.

Visit the following resources to learn more:

- [@official@Migrations](https://docs.djangoproject.com/en/6.0/topics/migrations/)
- [@article@Part-2: Migrations Files in Django Framework](https://medium.com/@altafkhan_24475/part-2-migrations-files-in-django-framework-486b9d4e173b)
- [@article@How To Get Up And Running With Django Migrations: A Guide](https://coderpad.io/blog/development/how-to-get-up-and-running-with-django-migrations-a-guide/)
## migrations@tCK6V3T4oGy9O8Wur2k9d

# Migrations

Migrations are Django's way of propagating changes you make to your models (like adding a field, deleting a model, etc.) into your database schema. They are essentially files that contain instructions on how to modify your database to match your model definitions. These files are generated based on the differences between your current models and the last known state of your database, allowing you to evolve your database schema over time in a controlled and reversible manner.

Visit the following resources to learn more:

- [@official@Migrations](https://docs.djangoproject.com/en/6.0/topics/migrations/)
- [@official@Migration Operations](https://docs.djangoproject.com/en/6.0/ref/migration-operations/)
- [@article@Mastering Django Migrations: A Complete Beginner’s Guide](https://medium.com/simform-engineering/mastering-django-migrations-a-complete-beginners-guide-a50d29924c7c)
- [@video@Django - What are migrations - actually? Introduction to migrations and the Django database](https://www.youtube.com/watch?v=N4gjiJumTZg)
## model-forms@HjcEX3u5iRSlq69U-pSEs

# Model Form Validation

ModelForm validation in Django involves ensuring that the data entered into a form, which is directly tied to a Django model, meets specific criteria before it's saved to the database. This process includes checking data types, lengths, and any custom validation rules defined in the model or the form itself, guaranteeing data integrity and preventing errors.

Visit the following resources to learn more:

- [@official@Creating forms from models](https://docs.djangoproject.com/en/6.0/topics/forms/modelforms/)
- [@article@Create Model Objects With a ModelForm](https://openclassrooms.com/en/courses/6967196-create-a-web-application-with-django/7349525-create-model-objects-with-a-modelform)
- [@article@ModelForm](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/Django/Forms#modelforms)
- [@video@Model Form | Django](https://www.youtube.com/watch?v=VOddmV4Xl1g)
## model-inheritance@SWNGsyrpP7XghRa_zKQbb

# Model Inheritance

Model inheritance in Django allows you to create new models that inherit fields and behaviors from existing models. This promotes code reuse and helps establish relationships between different data entities in your application. By inheriting from a base model, you can avoid redefining common fields and methods, making your code more organized and maintainable.

Visit the following resources to learn more:

- [@official@Model inheritance](https://docs.djangoproject.com/fr/2.2/topics/db/models/#model-inheritance)
- [@article@Understanding Django-Advanced Model Inheritance.](https://foysalff.medium.com/understanding-django-model-inheritance-b0c38588ebb4)
- [@article@Django Model Inheritance](https://dev.to/highcenburg/django-model-inheritance-4f3p)
- [@video@Django Model Inheritance Options Introduction - ORM Part-9](https://www.youtube.com/watch?v=4Xag2FzmN60)
## model-methods@NV1l8YU9CHw_I8NhhN0hO

# Model Methods

Model methods are functions you define within a Django model class to add custom behavior to individual model instances. These methods allow you to encapsulate logic related to a specific object, such as calculating derived values, performing data manipulations, or implementing custom validation rules. They provide a clean and organized way to extend the functionality of your models beyond the basic fields and relationships.

Visit the following resources to learn more:

- [@official@Model methods](https://docs.djangoproject.com/en/6.0/topics/db/models/#model-methods)
- [@article@An Overview of Django Model Methods in 2023](https://www.horilla.com/blogs/an-overview-of-django-model-methods-in-2023/)
- [@video@Django Model Properties & Methods | @property decorator | get_absolute_url() method](https://www.youtube.com/watch?v=PgHaH8tGdWw)
- [@video@Django Tutorial #11 - Model Methods](https://www.youtube.com/watch?v=ERCt6HUcaFw)
## model-relationships@D7wMA3PYw1RYMz9lXGsgW

# Model Relationships

Model relationships in Django define how different models (database tables) are connected. These relationships allow you to link related data, such as a blog post belonging to a specific author or a customer having multiple orders. Django provides different types of relationships like One-to-One, One-to-Many (ForeignKey), and Many-to-Many to represent these connections effectively in your database schema.

Visit the following resources to learn more:

- [@official@Relationships](https://docs.djangoproject.com/en/6.0/topics/db/models/#relationships)
- [@official@Examples of model relationship API usage](https://docs.djangoproject.com/en/6.0/topics/db/examples/)
- [@article@How to Define Relationships Between Django Models](https://www.freecodecamp.org/news/django-model-relationships/)
- [@video@Understanding Django Model Relationships](http://youtube.com/watch?v=2KqhBkMv7aM)
## models@iY7yJ9NN77F6wvlgD4zKG

# Models

Models are Python classes that represent database tables. Each model attribute represents a database field. Django uses these models to interact with the database, allowing you to create, read, update, and delete data without writing raw SQL queries. They define the structure of your data and provide a high-level interface for database operations.

Visit the following resources to learn more:

- [@official@Models](https://docs.djangoproject.com/en/6.0/topics/db/models/)
- [@article@Django Models](https://www.w3schools.com/django/django_models.php)
- [@article@Django Tutorial Part 3: Using models](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/Django/Models)
- [@video@Django Models | Crash Course | Field Types, Connections, and Model Functions](https://www.youtube.com/watch?v=RbJOmgTX63M)
## modelspy@WYPjCQcccmwcjnxM_5VkU

# Models.py

`models.py` is a Python file within a Django app that defines the structure of your application's data. It contains classes that represent database tables, with each class attribute representing a field in the table. These models allow you to interact with your database using Python code, abstracting away the complexities of raw SQL queries.

Visit the following resources to learn more:

- [@official@Models](https://docs.djangoproject.com/en/6.0/topics/db/models/)
- [@article@Django models](https://www.w3schools.com/django/django_models.php)
- [@article@What exactly is model.py and how does it works?](https://medium.com/@stefano.passaro/what-exactly-is-model-py-and-how-does-it-works-31c3ab35af11)
## mysql@pnyNAPLViP4LBGvkVbZ5s

# MySQL in Django

MySQL is a popular open-source relational database management system. Django supports MySQL as one of its database backends, allowing you to store and manage your application's data using MySQL's robust features. To use MySQL with Django, you'll need to install the appropriate MySQL driver, configure your Django project's settings to connect to the database, and then define your data models and interact with the database using Django's ORM.

Visit the following resources to learn more:

- [@official@MySQL Notes](https://docs.djangoproject.com/en/6.0/ref/databases/#mysql-notes)
- [@article@Beginner’s Django Guide: Setting Up Projects with MySQL](https://medium.com/@nikhilrpandey15/beginners-guide-to-django-setting-up-projects-with-mysql-03ff8cb43a44)
- [@article@Django-MySQL Documentation](https://django-mysql.readthedocs.io/en/latest/)
- [@video@How to Connect MySQL database with Django Project | Beginners Tutorial](https://www.youtube.com/watch?v=5g_xIwxLSJk)
## named-urls@3qImaY9Hs3Cvatw1X96Ns

# Named URLs

Named URLs in Django provide a way to refer to your URL patterns by name instead of hardcoding the URL strings in your templates and views. This allows you to change your URL structure without having to update every place where the URL is used, making your code more maintainable and less prone to errors. By assigning a unique name to each URL pattern, you can use this name to dynamically generate URLs, ensuring that your links remain consistent even if the underlying URL structure changes.

Visit the following resources to learn more:

- [@official@Naming URL patterns](https://docs.djangoproject.com/en/6.0/topics/http/urls/#naming-url-patterns)
- [@article@Named URL patterns](https://www.hostinger.com/my/tutorials/django-url-patterns#Named_URL_patterns)
- [@video@Django Tutorial #15 - Named URL's](https://www.youtube.com/watch?v=07YSCsscYhc)
- [@video@Django URLs - Named URLS, url template-tag, Reversing URLs, URL namespaces, & get_absolute_url()](https://www.youtube.com/watch?v=obRENgwHS7A)
## pagination@-ZFQ0QzqqBIuSQK9CwLg4

# Pagination

Pagination divides large datasets into smaller, discrete pages, improving user experience and server performance. In Django, this is typically used when displaying a large number of objects, such as blog posts or product listings. Instead of loading all items at once, pagination allows users to navigate through the data in manageable chunks, reducing load times and making it easier to find specific information.

Visit the following resources to learn more:

- [@official@Pagination](https://docs.djangoproject.com/en/6.0/topics/pagination/)
- [@official@Paginator](https://docs.djangoproject.com/en/6.0/ref/paginator/)
- [@article@Pagination in Django](https://testdriven.io/blog/django-pagination/)
- [@video@Pagination For Django - Django Wednesdays #18](https://www.youtube.com/watch?v=N-PB-HMFmdo)
## path-converters@NB50RuNBT5Oja2Ry6p892

# Path Converters

Path converters in Django are special strings within URL patterns that capture specific parts of the URL and pass them as arguments to your view functions. They define the type of data expected in that part of the URL (like an integer, string, or slug) and ensure that the data is correctly formatted before being passed to the view. This allows you to create dynamic URLs that can handle different types of input and simplifies the process of extracting data from the URL for use in your application logic.

Visit the following resources to learn more:

- [@official@Path converters](https://docs.djangoproject.com/en/6.0/topics/http/urls/#path-converters)
- [@article@Django: write a custom URL path converter to match given strings](https://adamj.eu/tech/2025/08/01/django-custom-url-converter-string/)
- [@article@Path Converters in Django: Customizing Your URL Patterns](https://python.plainenglish.io/path-converters-in-django-customizing-your-url-patterns-19791b6401f4)
- [@video@Django Path Converters - Built-in Converters and Writing Custom Converters!](https://www.youtube.com/watch?v=hrfqwj7JCAc)
## pdb-ipdb@WRHWs75DbhuiVZm1XMe7z

# PDB and IPDB

PDB (Python Debugger) is an interactive source code debugger for Python programs. It allows you to pause your program during execution, inspect variables, step through code line by line, and set breakpoints. IPDB is an enhanced version of PDB that uses IPython, providing features like tab completion, syntax highlighting, and better introspection capabilities, making the debugging process more efficient and user-friendly.

Visit the following resources to learn more:

- [@official@pdb](https://docs.python.org/3/library/pdb.html)
- [@official@ipdb](vhttps://pypi.org/project/ipdb/)
- [@article@Python Debugging With Pdb](https://realpython.com/python-debugging-pdb/)
- [@video@How to use ipdb the interactive python debugger](https://www.youtube.com/watch?v=EnC9ciDkXqA)
## postgresql@ykgvgR6YE_-V1LAtr0DvU

# PostgreSQL in Django

PostgreSQL is an open-source, advanced relational database management system (RDBMS) known for its reliability, data integrity, and adherence to standards. It offers a wide range of features, including support for complex data types, advanced indexing, and transactional integrity, making it a robust choice for managing structured data. Django fully supports PostgreSQL as one of its primary database backends.

Visit the following resources to learn more:

- [@roadmap@Visit the Dedicated PostgreSQL Roadmap](https://roadmap.sh/postgresql-dba)
- [@official@PostgreSQL Notes](https://docs.djangoproject.com/en/6.0/ref/databases/#postgresql-notes)
- [@article@Complete Tutorial: Set-up PostgreSQL Database with Django Application](https://medium.com/django-unleashed/complete-tutorial-set-up-postgresql-database-with-django-application-d9e789ffa384)
- [@video@Django PostgreSQL | Django PostgreSQL Database Setup](https://www.youtube.com/watch?v=FlzfWgVZuyY)
## production-checklist@PsDSs7qC_M3l-Ang1wTZe

# Production Checklist

A production checklist is a structured list of tasks and configurations that need to be verified and completed before deploying a Django application to a live, production environment. It ensures that the application is secure, performant, and reliable for end-users by covering aspects like security settings, database configurations, static file handling, and monitoring setup.

Visit the following resources to learn more:

- [@official@Deployment checklist](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/)
- [@article@The Django Deployment Checklist: Zero to Production in 30 Minutes](https://medium.com/@anas-issath/the-django-deployment-checklist-zero-to-production-in-30-minutes-50d176a96560)
## projects--apps@d0JBAP2Sot-u4diwqDYIq

# Projects & Apps

In Django, a project is a collection of settings and configurations for a particular website or web application. An app, on the other hand, is a modular, reusable component that performs a specific function within that project, like handling user authentication, managing blog posts, or processing payments. A project can contain multiple apps, and an app can be used in multiple projects.

Visit the following resources to learn more:

- [@official@Writing your first Django app, part 1](https://docs.djangoproject.com/en/6.0/intro/tutorial01/)
- [@official@Django Create Project](https://www.w3schools.com/django/django_create_project.php)
- [@video@How to Create First Django Project in Visual Studio Code (2024)](https://www.youtube.com/watch?v=fxcOtcYYqA0)
## pytest@K2dNQ69laFT853CFniJrZ

# pytest

pytest is a popular Python testing framework that simplifies writing and running tests. It offers features like auto-discovery of test functions, simple assertion syntax, extensive plugin support, and detailed error reporting. pytest aims to make testing more efficient and readable, allowing developers to focus on verifying the correctness of their code.

Visit the following resources to learn more:

- [@official@pytest-django Documentation](https://pytest-django.readthedocs.io/en/latest/)
- [@opensource@pytest](https://github.com/pytest-dev/pytest)
- [@article@How to Use Pytest for Unit Testing](https://www.datacamp.com/tutorial/pytest-tutorial-a-hands-on-guide-to-unit-testing)
- [@video@Pytest Mastery with Django](https://www.youtube.com/watch?v=LYX6nlECcro&list=PLOLrQ9Pn6caw3ilqDR8_qezp76QuEOlHY)
## query-optimization@u2bq7WaT2aSbrSaa0yB86

# Query Optimization

Query optimization is the process of improving the efficiency of database queries to reduce execution time and resource consumption. It involves analyzing queries, identifying bottlenecks, and applying techniques like indexing, query rewriting, and caching to minimize the amount of data processed and the number of database operations performed. The goal is to make queries run faster and more efficiently, leading to improved application performance and scalability.

Visit the following resources to learn more:

- [@official@Database access optimization](https://docs.djangoproject.com/en/6.0/topics/db/optimization/)
- [@article@Django Query Optimization - Defer, Only, and Exclude](https://testdriven.io/blog/django-query-optimization/)
- [@article@Fine-Tuning Django ORM: Proven Optimization Techniques](https://medium.com/simform-engineering/django-orm-optimization-5763f3915365)
- [@video@Django Query Optimization / select_related & prefetch_related / django-debug-toolbar / N+1 Problem](https://www.youtube.com/watch?v=a3dTy8RO5Ho)
## querying-data@8ud6LNbixJEP1It9AUMB7

# Querying Data with Django ORM

The Django ORM (Object-Relational Mapper) provides a powerful and convenient way to interact with your database. Instead of writing raw SQL queries, you use Python code to retrieve data from your models. This involves using methods like `filter()`, `get()`, `all()`, and `exclude()` on your model's manager (usually `objects`) to specify the conditions for the data you want to retrieve. These methods return QuerySets, which are lazy-evaluated collections of model instances that match your criteria.

Visit the following resources to learn more:

- [@official@Making Queries](https://docs.djangoproject.com/en/6.0/topics/db/queries/#retrieving-objects)
- [@article@An introduction to the Django ORM](https://opensource.com/article/17/11/django-orm)
- [@video@Django ORM Mastery Series](https://www.youtube.com/playlist?list=PLOLrQ9Pn6cazjoDEnwzcdWWf4SNS0QZml)
## raw-sql@7rCNwoQW2lI7xxMUP_ESa

# Raw SQL Queries

Raw SQL queries in Django allow you to bypass the Django ORM and write SQL statements directly. This is useful when you need to optimize performance, access database-specific features not supported by the ORM, or execute complex queries that are difficult to express using the ORM's query API. It provides a way to interact with the database at a lower level, giving you more control over the generated SQL.

Visit the following resources to learn more:

- [@official@Performing raw SQL queries](https://docs.djangoproject.com/en/6.0/topics/db/sql/)
- [@article@Django Running Raw Queries](https://www.scaler.com/topics/django/django-running-raw-queries/)
- [@video@Django ORM - Performing raw SQL queries](https://www.youtube.com/watch?v=iWDvsMOngxk)
## regex-paths@DbJ1BIOoerkCH4P95Z7wD

# Regex Paths

Regular expression paths in Django provide a powerful and flexible way to define URL patterns. Instead of using simple string matching, you can use regular expressions to capture specific parts of the URL and pass them as arguments to your view functions. This allows you to create dynamic and complex URL structures that can handle a wide range of user requests.

Visit the following resources to learn more:

- [@official@Using regular expressions](https://docs.djangoproject.com/en/6.0/topics/http/urls/#using-regular-expressions)
- [@article@Understanding Django URL patterns](https://www.hostinger.com/my/tutorials/django-url-patterns)
- [@article@How Django URLs work with Regular Expressions](https://www.codingforentrepreneurs.com/blog/how-django-urls-work-with-regular-expressions)
- [@video@How Django URLs work with Regular Expressions](https://www.youtube.com/watch?v=8rExil_EWtk)
## request-reponse-flow@ftFF3oFfqpKvjQhXk3bWw

# Request-Response Flow in Django

The request-response flow describes how a web application handles incoming requests from users and generates appropriate responses. When a user interacts with a website (e.g., clicks a link or submits a form), their browser sends a request to the server. The server then processes this request, potentially interacting with a database or other resources, and ultimately sends back a response to the user's browser, which then renders the content for the user to see.

Visit the following resources to learn more:

- [@official@Request and response objects](https://docs.djangoproject.com/en/6.0/ref/request-response/)
- [@article@Django Request-Response Cycle?](https://medium.com/@developerstacks/django-request-response-cycle-7165167f54c5)
- [@article@Django Request Life Cycle Explained](https://dev.to/nilebits/django-request-life-cycle-explained-ci6)
- [@video@Python Django Course | Understanding the Django Request Response Cycle](https://www.youtube.com/watch?v=9X83BZ1cF7o)
## reverse-url@KlEgfzfkPu0O43tJIsU3H

# Reverse URL

Reverse URL resolution is the process of generating URLs from their names and arguments, instead of hardcoding them directly into your templates or views. This allows you to make changes to your URL patterns without having to update every part of your application that uses those URLs. By using named URL patterns, you can dynamically construct URLs based on the current configuration, making your application more maintainable and flexible.

Visit the following resources to learn more:

- [@official@Reverse resolution of URLs](https://docs.djangoproject.com/en/6.0/topics/http/urls/#reverse-resolution-of-urls)
- [@article@Django Reverse](https://www.scaler.com/topics/django/django-reverse/)
- [@video@45 - Django URLs Reverse - Python & Django 3.2 Tutorial Series](https://www.youtube.com/watch?v=rm2YTMc2s10)
## routers@1p5abgLJ31IRTUiFwbeSa

# Routers in Django REST Framework

Routers in Django REST Framework (DRF) provide an automated way to generate URL patterns for your API views. Instead of manually defining URLs for common API actions like listing, creating, retrieving, updating, and deleting resources, routers handle this automatically based on the viewsets you define. This simplifies URL configuration and promotes consistency across your API.

Visit the following resources to learn more:

- [@official@Routers](https://www.django-rest-framework.org/api-guide/routers/)
- [@article@Django REST Framework: ViewSets and Routers Explained (Part 2)](https://medium.com/@michal.drozdze/django-rest-framework-viewsets-and-routers-explained-part-2-4d866a0ab5e1)
- [@video@Viewsets & Routers in Django REST Framework](https://www.youtube.com/watch?v=4MrB4IvW6Ow)
## routing-middleware@kVhW3uJawiK1waW-2Gk7F

# Routing Middleware

Middleware in Django is a framework of hooks into Django's request/response processing. It's a layer of code that sits between the web server and your Django views, processing every request and response in your application. This allows you to modify the request before it reaches your view, or modify the response before it's sent to the user, enabling functionalities like authentication, session management, and request logging.

Visit the following resources to learn more:

- [@official@Middleware](https://docs.djangoproject.com/en/6.0/topics/http/middleware/)
- [@article@Understanding Django Middleware: How to Create Custom Middleware](https://medium.com/@farad.dev/understanding-django-middleware-how-to-create-custom-middleware-789744722df3)
- [@video@Writing Django Middleware (with tests!) | HTMX middleware | IP Blacklist middleware](https://www.youtube.com/watch?v=--ddZc39wVQ)
## running-your-project@QJJh0Dl4IT_I3_eACrStj

# Running Your Django Project

Running a Django project involves starting a local development server that allows you to view and interact with your web application in a browser. This server listens for incoming requests and serves the appropriate content, enabling you to test and debug your project during development. It's a crucial step in the Django development workflow, allowing you to see your code in action.

Visit the following resources to learn more:

- [@official@Writing your first Django app, part 1](https://docs.djangoproject.com/en/6.0/intro/tutorial01/)
- [@article@Django Create Project](https://www.w3schools.com/django/django_create_project.php)
- [@video@How to Start a Django Project and Run the Development Server](https://www.youtube.com/watch?v=PBh6XkFobes)
- [@video@How to Create First Django Project in Visual Studio Code (2024)](https://www.youtube.com/watch?v=fxcOtcYYqA0)
## serializers@aJ0jM_zjUJkt0wVfJQYt7

# Serializers

Serializers in Django REST Framework transform complex data, like querysets and model instances, into Python datatypes that can be easily rendered into JSON, XML, or other content types. They also handle the reverse process, allowing parsed data to be converted back into model instances after validation. This makes them essential for building RESTful APIs that can both receive and send data in a structured and manageable way.

Visit the following resources to learn more:

- [@official@Serializers](https://www.django-rest-framework.org/api-guide/serializers/)
- [@official@Tutorial 1: Serialization](https://www.django-rest-framework.org/tutorial/1-serialization/)
- [@official@Serializer relations](https://www.django-rest-framework.org/api-guide/relations/)
- [@video@Django REST Framework- Nested Serializers, SerializerMethodField and Serializer Relations](https://www.youtube.com/watch?v=KfSYadIFHgY)
## setting-up-the-database@yRaVL7FoWcHb2A8uz5TV8

# Database Setup in Django

Setting up the database in Django involves configuring your project to connect to and interact with a specific database management system (DBMS). This process includes specifying the database type (e.g., PostgreSQL, MySQL, SQLite), providing connection details like the database name, username, password, and host, and ensuring that Django can communicate with the database to store and retrieve data for your application.

Visit the following resources to learn more:

- [@roadmap@Visit the Dedicated SQL Roadmap](https://roadmap.sh/sql)
- [@official@Databases](https://docs.djangoproject.com/en/6.0/ref/databases/)
- [@official@Writing your first Django app, part 2](https://docs.djangoproject.com/en/6.0/intro/tutorial02/)
- [@video@Django Tutorial #4 - Database Setup](https://www.youtube.com/watch?v=DZVFgMSyRXI)
## settingspy@_RRCcJpO33XAgdsBzJdY9

# settings.py

`settings.py` is a crucial Python module in a Django project that contains global configurations and settings for the entire application. It defines things like database connections, installed apps, middleware, template locations, and security settings. This file essentially acts as the central control panel for your Django project, allowing you to customize its behavior and functionality.

Visit the following resources to learn more:

- [@official@Django settings](https://docs.djangoproject.com/en/6.0/topics/settings/)
- [@article@Understanding Django's settings.py File: A Comprehensive Guide for Beginners](https://dev.to/rupesh_mishra/understanding-djangos-settingspy-file-a-comprehensive-guide-for-beginners-35e2)
- [@article@How to Set Environment Variables in Python (Step-by-Step)](https://roadmap.sh/python/set-environment-variable)
- [@video@settings.py configuration in django | django settings.py explained | django full tutorial | #04](https://www.youtube.com/watch?v=uGcmzeU1tmQ)
## signals@gPy4yi6smV4gcRj_WCqYR

# Signals

Signals in Django allow certain actions to be triggered when specific events occur in your application. Think of them as a way to let different parts of your code communicate with each other without being directly linked. When a particular event happens (like a model being saved or deleted), a signal is sent out, and any functions that are connected to that signal will be executed. This provides a decoupled way to perform tasks in response to events throughout your Django project.

Visit the following resources to learn more:

- [@official@Signals](https://docs.djangoproject.com/en/6.0/topics/signals/)
- [@official@Signal List](https://docs.djangoproject.com/en/6.0/ref/signals/)
- [@article@How to Use Django Signals in Your Projects](https://www.freecodecamp.org/news/how-to-use-django-signals-in-your-projects/)
- [@video@Django Signals](https://www.youtube.com/watch?v=rEX50LJrFuU&list=PL0efIqwJO9kDGQ34csSYNSm2udR4kOrdb)
## sqlite@o6qNq8D_gwC5UrkKjz57o

# SQLite in Django

SQLite is a self-contained, serverless, zero-configuration, transactional SQL database engine. It's embedded directly into the application, meaning it doesn't require a separate server process to operate. This makes it a lightweight and convenient choice for development, testing, and small-scale Django projects.

Visit the following resources to learn more:

- [@official@SQLite notes](https://docs.djangoproject.com/en/6.0/ref/databases/#sqlite-notes)
- [@article@The definitive guide to using Django with SQLite in production](https://alldjango.com/articles/definitive-guide-to-using-django-sqlite-in-production)
- [@article@“Using SQLite as a Database Backend in Django Projects” ||Code with Bushra](https://medium.com/@codewithbushra/using-sqlite-as-a-database-backend-in-django-projects-code-with-bushra-d23e3100686e)
- [@video@Django Part 3: Sqlite3 Database and Migrations](https://www.youtube.com/watch?v=RzkVbz7Ie44)
## static-files@MJIQZoLMiURPrhqMUddG7

# Static Files

Static files in web development refer to the unchanging assets that make up the user interface of a website, such as images, CSS stylesheets, JavaScript files, and fonts. These files are served directly to the user's browser without requiring any server-side processing, contributing to the overall look, feel, and functionality of the website.

Visit the following resources to learn more:

- [@official@How to manage static files (e.g. images, JavaScript, CSS)](https://docs.djangoproject.com/en/6.0/howto/static-files/)
- [@article@Working with Static and Media Files in Django](https://testdriven.io/blog/django-static-files/)
- [@article@Django - Add Static File](https://www.w3schools.com/django/django_add_static_files.php)
- [@video@Django Tutorial #8 - Static Assets](https://www.youtube.com/watch?v=kJJx77PYMFA)
## static@k7aMrFNIY11_bD_XwVLv7

# Static Files

Within a Django project, the `static` folder is where you store static files like CSS stylesheets, JavaScript files, images, and fonts. These files are essential for styling and adding interactivity to your web application's user interface. Django needs to know where to find these files to serve them correctly to the browser, and the `static` folder, usually located within each app directory, provides a standardized location for this purpose.

Visit the following resources to learn more:

- [@official@How to manage static files (e.g. images, JavaScript, CSS)](https://docs.djangoproject.com/en/6.0/howto/static-files/)
- [@article@Working with Static and Media Files in Django](https://testdriven.io/blog/django-static-files/)
## tags--custom-tags@W2v9_4sn5aoZjxMKOQTcw

# Tags & Custom Tags

Tags are control structures that Django's template engine uses to perform actions like looping, variable assignment, or conditional logic within templates. Custom tags allow developers to extend the template language by defining their own tags to perform specific tasks or render complex data in a reusable way.

Visit the following resources to learn more:

- [@official@Built-in template tags and filters](https://docs.djangoproject.com/en/6.0/ref/templates/builtins/)
- [@official@How to create custom template tags and filters](https://docs.djangoproject.com/en/6.0/howto/custom-template-tags/)
- [@article@Understanding and Implementing Custom Template Tags in Django](https://dev.to/3bdelrahman/understanding-and-implementing-custom-template-tags-in-django-5cao)
- [@video@Django Tutorial #10 - Template Tags](https://www.youtube.com/watch?v=RCE3VUpzGw0)
## template-inheritance@4j0fCRER1a_c7FY06Q68h

# Template Inheritance

Template inheritance in Django allows you to build a base "skeleton" template that contains all the common elements of your site (like the header, footer, and navigation). Child templates can then extend this base template and override specific blocks of content, filling in the unique parts for each page while reusing the common structure. This promotes code reusability and maintainability by avoiding repetition across your website's templates.

Visit the following resources to learn more:

- [@official@Template Inheritance](https://docs.djangoproject.com/en/6.0/ref/templates/language/#id1)
- [@article@Understanding Django template inheritance](https://dev.to/doridoro/understanding-django-template-inheritance-d8c)
- [@article@extends Template Tag](https://www.w3schools.com/django/ref_tags_extends.php)
- [@video@Django Template Inheritance Explained](https://www.youtube.com/watch?v=mxbzt7wodAs)
## templates@v5skymtqU7PmMuBsl-1rX

# Templates

Templates are text files that separate the presentation of your application from its Python code. They contain placeholders (variables) and logic (template tags) that are evaluated when the template is rendered, dynamically generating HTML or other text-based formats. This allows you to create dynamic web pages by inserting data from your Django application into a predefined structure.

Visit the following resources to learn more:

- [@official@Templates](https://docs.djangoproject.com/en/6.0/topics/templates/)
- [@article@The Ultimate Guide to Django Templates](https://blog.jetbrains.com/pycharm/2025/02/the-ultimate-guide-to-django-templates/)
- [@article@Django Templates](https://www.w3schools.com/django/django_templates.php)
- [@video@Django Tutorial - Templates & Custom HTML](https://www.youtube.com/watch?v=b0CgA_Ap_Mc)
## templates@YLvdL6lwZk2vlMK7QaTk7

# Templates

The `templates` folder in a Django project is where you store your HTML files. These HTML files define the structure and content of your web pages. Django uses a template engine to dynamically insert data from your Python code into these HTML files before sending them to the user's browser. This allows you to create dynamic and personalized web pages.

Visit the following resources to learn more:

- [@official@Templates](https://docs.djangoproject.com/en/6.0/topics/templates/)
- [@article@The Ultimate Guide to Django Templates](https://blog.jetbrains.com/pycharm/2025/02/the-ultimate-guide-to-django-templates/)
## testspy@g-KGkdGeCJQe6NMe82gR8

# tests.py

`tests.py` is a Python file within a Django app's directory that is dedicated to containing tests for that specific app. It allows developers to write and execute automated tests to ensure the app's functionality works as expected, covering various aspects like models, views, and forms. These tests help prevent bugs, ensure code quality, and facilitate easier refactoring and maintenance.

Visit the following resources to learn more:

- [@official@Writing and running tests](https://docs.djangoproject.com/en/6.0/topics/testing/overview/)
- [@video@Testing in Django Tutorial #4 - Django Testing Basics](https://www.youtube.com/watch?v=QklKI2etw30)
## the-mvc-model@CXrUh4hBN7fhXShUhtO5n

# The MCV Model

The Model-View-Controller (MVC) architectural pattern separates an application into three interconnected parts. The Model manages data and business logic, the View displays data to the user, and the Controller handles user input and updates the Model. Django uses a slightly modified version called Model-Template-View (MTV), where the Template is the presentation layer (like the View in MVC), and the View handles the logic of what data to display (like the Controller in MVC). Django's framework structure naturally encourages this separation of concerns, making it easier to develop and maintain complex web applications.
## transactions@OoboX9UxuQ0pgjwQZmjIV

# Transactions

Transactions are a way to group a series of database operations into a single unit of work. This means that either all the operations within the transaction succeed, or none of them do. If any operation fails, the database rolls back to its previous state, ensuring data consistency and integrity. This is particularly useful when performing multiple related database updates, where a failure in one update could leave the database in an inconsistent state.

Visit the following resources to learn more:

- [@official@Database transactions](https://docs.djangoproject.com/en/6.0/topics/db/transactions/)
- [@article@Understanding Django’s Transaction Atomic](https://plainenglish.io/blog/understanding-djangos-transaction-atomic)
- [@article@Python: How Django Transactions Work](https://m-t-a.medium.com/python-how-django-transactions-work-a87083303102)
- [@video@Django Database Transactions / atomic() function](https://www.youtube.com/watch?v=L8k8Ukw1P6U)
## unittest--testcase@iKzWEV8ymBEh_J2ppKZjF

# unittest & TestCase

`unittest` is Python's built-in testing framework, providing a standard way to write and run tests. `TestCase` is a class within `unittest` that's used as a base class for creating individual test cases. You define methods within your `TestCase` subclass that represent specific tests, using assertions to check for expected outcomes.

Visit the following resources to learn more:

- [@official@Writing and running tests](https://docs.djangoproject.com/en/6.0/topics/testing/overview/)
- [@article@Django Testing with unittest](https://medium.com/@hmbarotov/django-testing-with-unittest-f797c746bfe0)
- [@video@Testing in Django Tutorial #3 - The Python unittest Module](https://www.youtube.com/watch?v=Ob25drPBgu0)
- [@video@Testing in Django Tutorial #4 - Django Testing Basics](https://www.youtube.com/watch?v=QklKI2etw30)
## updateview@vS0Y5DmrAEwoQ9gblM-8Q

# UpdateView

UpdateView is a class-based view in Django that simplifies the process of creating a view to handle updating an existing model instance. It provides a pre-built structure for displaying a form populated with the instance's data, processing the form submission, validating the data, and saving the updated instance to the database. This reduces the amount of boilerplate code needed for common update operations.

Visit the following resources to learn more:

- [@official@UpdateView](https://docs.djangoproject.com/en/6.0/ref/class-based-views/generic-editing/#django.views.generic.edit.UpdateView)
- [@article@A Brief Look at Django’s UpdateView](https://medium.com/@zarker24/a-brief-look-at-djangos-updateview-8a732d5d2c5b)
- [@article@Django Tutorial for Beginners - 32 - UpdateView and DeleteView](https://www.youtube.com/watch?v=5Ez2NXOX9zY)
- [@video@Learn Django Class Based Views - UpdateView - Theory and Examples](https://www.youtube.com/watch?v=EUUjJdw3EBM)
## url-patterns@ThYltfCyVKkKL_6jY2g-d

# URL patterns

URL patterns in Django define how URLs (web addresses) are mapped to specific views (functions that handle requests). They act like a directory, telling Django which view to execute when a user visits a particular URL. Each pattern consists of a regular expression that matches a URL and a corresponding view function. When a URL matches a pattern, Django calls the associated view, passing the request object and any captured parameters from the URL.

Visit the following resources to learn more:

- [@official@URL dispatcher](https://docs.djangoproject.com/en/6.0/topics/http/urls/)
- [@article@Django URLs](https://tutorial.djangogirls.org/en/django_urls/)
- [@article@Understanding Django URL patterns](https://www.hostinger.com/in/tutorials/django-url-patterns)
- [@video@Django Tutorial for Beginners 3 - URL dispatcher | Requests and Responses](https://www.youtube.com/watch?v=Y82NaZ2VZjE)
## urlspy@6y3ZnxclaV6JVGhUkQMtB

# urls.py in Django Apps

In Django, the `urls.py` file within an app is responsible for defining the URL patterns for that specific app. It acts as a table of contents, mapping URL paths to specific views (functions or classes) that handle the corresponding requests. This file essentially tells Django what code to execute when a user visits a particular URL within the app's scope.

Visit the following resources to learn more:

- [@article@Part-2: Migrations Files in Django Framework](https://medium.com/django-unleashed/django-project-structure-a-comprehensive-guide-4b2ddbf2b6b8)
- [@video@The Structure of a Django Application](https://www.youtube.com/watch?v=jmX27FrCqqs)
## urlspy@b9VXaPBraxAakcwHkyRYu

# URL Configuration in Django

In a Django project, `urls.py` files are responsible for mapping URL patterns to specific views. They act as a table of contents for your website, telling Django which view function to execute when a user visits a particular URL. Essentially, they define the structure of your website's addressable locations and how Django handles requests to those locations.

Visit the following resources to learn more:

- [@article@Django URLs](https://www.w3schools.com/django/django_urls.php)
- [@article@Django URLs](https://tutorial.djangogirls.org/en/django_urls/)
## users--permissions@hxVeLMj_jQYPNqMPcT8FW

# Users & Permissions

User authentication and authorization are fundamental aspects of web application security. Django provides a built-in system for managing users, groups, and permissions, allowing developers to control access to different parts of their application. This system defines who can access what, ensuring data integrity and security.

Visit the following resources to learn more:

- [@official@Using the Django authentication system](https://docs.djangoproject.com/en/6.0/topics/auth/default/#auth-admin)
- [@article@Django Tutorial Part 8: User authentication and permissions](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/Django/Authentication)
- [@video@Django Permissions system - deep dive with Users, Groups and Permissions](https://www.youtube.com/watch?v=IF_ZpCiZKkw)
## variables@wxkaVWdZGcAZVxbfOJvZE

# Variables in Django Templates

Variables in Django templates are placeholders that get replaced with actual values when the template is rendered. They allow you to dynamically display data from your Django views within your HTML templates. These variables are enclosed in double curly braces `{{ variable_name }}` and can represent data of various types, such as strings, numbers, lists, or even objects.

Visit the following resources to learn more:

- [@official@Variables](https://docs.djangoproject.com/en/6.0/ref/templates/language/#variables)
- [@article@Django Template Variables](https://www.w3schools.com/django/django_template_variables.php)
- [@video@Passing Variables to a Template with Django](https://www.youtube.com/watch?v=wkTE2QvzSmc)
## views--viewsets@MY9L0_kzjrbda43d-Ey-H

# Views & ViewSets

Views in Django REST Framework handle the logic for processing incoming web requests and returning responses, similar to regular Django views. ViewSets provide a way to group related views into a single class, reducing code duplication and simplifying the creation of complex APIs by offering pre-built actions like list, create, retrieve, update, and delete.

Visit the following resources to learn more:

- [@official@Viewsets](https://www.django-rest-framework.org/api-guide/viewsets/)
- [@official@Tutorial 6: ViewSets & Routers](https://www.django-rest-framework.org/tutorial/6-viewsets-and-routers/)
- [@article@Django REST Framework Views - ViewSets](https://testdriven.io/blog/drf-views-part-3/)
- [@video@Viewsets & Routers in Django REST Framework](https://www.youtube.com/watch?v=4MrB4IvW6Ow)
## views@04iZjMANQFOjASGRz9Maw

# Views

Views are functions or classes in Django that take a web request and return a web response. They act as the intermediary between the model (data) and the template (presentation), processing user requests, retrieving data from the database, and rendering the appropriate template to display the information to the user. Essentially, a view determines what content is shown to the user when they visit a specific URL.

Visit the following resources to learn more:

- [@official@Views](https://docs.djangoproject.com/en/6.0/topics/http/views/)
- [@article@Django Views](https://www.w3schools.com/django/django_views.php)
- [@article@Django Views — The Right Way¶](https://spookylukey.github.io/django-views-the-right-way/)
- [@video@Django Tutorial #3 - URLs and Views](https://www.youtube.com/watch?v=TblSa29DX6I)
## viewspy@e-5mm0hv-sgG4lfDcISQ6

# Views

`views.py` is a Python file in a Django app that contains the logic for handling web requests and returning responses. It defines functions or classes, known as "views," that receive HTTP requests, process data (often interacting with models), and render templates to generate HTML responses that are sent back to the user's browser. Essentially, it acts as the intermediary between the user's request and the data/templates needed to fulfill that request.

Visit the following resources to learn more:

- [@official@Views](https://docs.djangoproject.com/en/6.0/topics/http/views/)
- [@article@Django Views](https://www.w3schools.com/django/django_views.php)
- [@article@Django Views — The Right Way](https://spookylukey.github.io/django-views-the-right-way/index.html)
## virtual-envs@1JeM23O8r_WnIdmgrgZ_7

# Virtual Environments

Virtual environments are isolated spaces on your computer that contain specific versions of Python and its packages. This allows you to manage dependencies for different projects separately, preventing conflicts that can arise when projects require different versions of the same library. By creating a virtual environment for each Django project, you ensure that each project has its own set of dependencies, making your projects more organized and reproducible.

Visit the following resources to learn more:

- [@article@How to Activate Your Django Virtual Environment](https://www.freecodecamp.org/news/how-to-activate-your-django-virtual-environment/)
- [@article@Django - Create Virtual Environment](https://www.w3schools.com/django/django_create_virtual_environment.php)
- [@article@Setting up a Django development environment](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/Django/development_environment)
- [@video@How to Install Django in Virtual Environment in VSCode (2024)](https://www.youtube.com/watch?v=EjIoERmeVE8)
## whitenoise@oUjfjCRymVJs4HzmMeks5

# Whitenoise

Whitenoise is a library that allows your web application to serve static files directly from its own WSGI server. This means you don't need to rely on a separate web server like Nginx or Apache to serve static assets such as CSS, JavaScript, and images. It simplifies deployment, especially in environments where configuring a separate static file server is complex or undesirable.

Visit the following resources to learn more:

- [@official@WhiteNoise Docs](https://whitenoise.readthedocs.io/en/stable/index.html)
- [@official@whitenoise](https://pypi.org/project/whitenoise/)
- [@article@Django - Installing WhiteNoise](https://www.w3schools.com/django/django_static_whitenoise.php)
- [@video@Whitenoise for Django Static Assets - Overview!](https://www.youtube.com/watch?v=QZTk8txo6x0)
## why-use-web-frameworks@xdxitF1Foo6W9Pj6-2Be1

# Web Frameworks

Web frameworks provide a structure and set of tools to streamline the development of web applications. They handle common tasks like routing URLs, managing sessions, interacting with databases, and ensuring security, allowing developers to focus on the unique features of their application rather than reinventing the wheel. This leads to faster development, more maintainable code, and improved security practices.

Visit the following resources to learn more:

- [@article@Web Frameworks: All You Should Know About](https://www.browserstack.com/guide/web-development-frameworks)
- [@article@What is a web development framework (WDF)?](https://www.techtarget.com/searchcontentmanagement/definition/web-development-framework-WDF)
- [@video@hat Is a Framework in Programming? | Why Is It Useful?](https://www.youtube.com/watch?v=BfhSoFARn6w)