from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .models import CarModel, CarMake, CarDealer, DealerReview
from .restapis import get_dealer_by_id, get_dealers_from_cf, get_dealers_by_state, get_dealer_reviews_from_cf, post_request
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseServerError


# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create an `about` view to render a static about page
def about(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/about.html', context)


# Create a `contact` view to return a static contact page
def contact(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/contact.html', context)


# Create a `login_request` view to handle sign in request
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponse("User successfully logged in.")
        else:
            return HttpResponse("Invalid username or password.")
    else:
        # Render the login form
        return render(request, 'login.html')


# Create a `logout_request` view to handle sign out request
def signout_view(request):
    logout(request)
    return redirect('djangoapp:index')  # Redirect to index page after logout


def signup_view(request):
    context = {}
    # If it is a GET request, just render the registration page
    if request.method == 'GET':
        return render(request, 'djangoapp/signup.html', context)
    # If it is a POST request
    elif request.method == 'POST':
        # Get user information from request.POST
        username = request.POST['username']
        password = request.POST['password']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        user_exist = False
        try:
            # Check if user already exists
            User.objects.get(username=username)
            user_exist = True
        except:
            # If not, simply log this is a new user
            logger.debug("{} is new user".format(username))
        # If it is a new user
        if not user_exist:
            # Create user in auth_user table
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            # Login the user and redirect to course list page
            login(request, user)
            messages.success(request, 'Your account was created successfully.')
            return redirect("/djangoapp/")
        else:
            return render(request, 'djangoapp/signup.html', context)


# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    if request.method == "GET":
        context = {}
        url = "https://markoweissma-3000.theiadockernext-1-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/dealerships/get"
        # Get dealers from the URL
        dealerships = get_dealers_from_cf(url)
        context["dealerships"] = get_dealers_from_cf(url)
        # Add debugging output
        print("Dealerships:", dealerships)
        # Concat all dealer's short name
        dealer_names = ' '.join([dealer.short_name for dealer in dealerships])
        # Return a list of dealer short name
        return render(request, 'djangoapp/index.html', context)
     


# Create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, dealer_id):
    print(f"get_dealer_details view called with dealer_id: {dealer_id}")
    if request.method == "GET":
        context = {}
        dealer_url = "https://markoweissma-3000.theiadockernext-1-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/dealerships/get"
        reviews_url = "https://markoweissma-5000.theiadockernext-1-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/api/get_reviews"
       
        dealerships = get_dealers_from_cf(dealer_url, id=dealer_id)
        print("Dealerships:", dealerships)
       
        if dealerships:
            context['dealership'] = dealerships[0]
            print(f"Dealship Name: {dealerships[0].full_name}")
            context['dealer_id'] = dealer_id
        else:
            context['dealership'] = None
            context['dealer_id'] = dealer_id
            # or return a response indicating that the dealership was not found
       
        # Remove 'id=' from the argument since it's already a positional argument
        try:
            dealership_reviews_response = get_dealer_reviews_from_cf(reviews_url, dealer_id)
            print("Dealership Reviews API Response Content:", dealership_reviews_response)

            if isinstance(dealership_reviews_response, list):
                if dealership_reviews_response:
                    print("Dealership Reviews API Response Content:", dealership_reviews_response)
                    context['reviews'] = dealership_reviews_response
                    print("Context:", context)
                else:
                    print("Dealership Reviews API Response: Empty list")
                    context['reviews'] = []
            else:
                print("Invalid Dealership Reviews API Response:", dealership_reviews_response)
                context['reviews'] = []
        except Exception as e:
            print(f"Error getting reviews from API: {e}")
            context['reviews'] = []

        return render(request, 'djangoapp/dealer_details.html', context)



# Create a `add_review` view to submit a review
def add_review(request, dealer_id):
    if request.method == "GET":
        context = {}
        dealer_url = "https://markoweissma-3000.theiadockernext-1-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/dealerships/get"
        dealerships = get_dealers_from_cf(dealer_url, id=dealer_id)
        car_models = CarModel.objects.filter(dealer_id=dealer_id)
        context['cars'] = car_models
        context['dealer_id'] = dealer_id

        # Check if there are dealerships before accessing the first one
        if dealerships:
            context['dealer'] = dealerships[0]
        else:
            context['dealer'] = None  # Handle the case where there are no dealerships

        return render(request, 'djangoapp/add_review.html', context)
    elif request.method == "POST":
        logging.info("POST data received:")
        logging.info(request.POST)
        if request.user.is_authenticated:
            url = "https://markoweissma-5000.theiadockernext-1-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/api/post_review"
            review = dict()
            review["id"] = 1
            review["dealership"] = dealer_id
            review["name"] = request.POST.get('content')
            review["review"] = request.POST.get('content')
            review["purchase"] = request.POST.get('purchasecheck') == "on"
            review["purchase_date"] = request.POST.get('purchasedate')
            car_models = CarModel.objects.filter(id=request.POST.get('car'))
            car_model = car_models[0]
            if car_model.car_make:
                review["car_make"] = car_model.car_make.name
            else:
                review["car_make"] = None
            review["car_model"] = car_model.name
            review["car_year"] = str(car_model.year)[0:4]
            print(review)
            response = post_request(url, review, dealerId=dealer_id)
            print(response)
        return redirect("djangoapp:dealer_details", dealer_id=dealer_id)
