import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:firebase_database/firebase_database.dart';
import 'package:geolocator/geolocator.dart';
import 'dart:math' show cos, sqrt, asin;

void main() async{
  runApp(MyApp());
}

class MyApp extends StatefulWidget {
  @override
  _MyAppState createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  Completer<GoogleMapController> _controller = Completer();
  static const LatLng _center = const LatLng(24.9670568, 121.1869849);
  //static const LatLng _dog = const LatLng(24.98, 121.20);
  Set<Marker> markers = Set();
  BitmapDescriptor pinLocationIcon;
  final DatabaseReference fireBaseDB = FirebaseDatabase.instance.reference();
  StreamSubscription<Event> fireBaseDBSubScription;
  MapType _currentMapType = MapType.normal;
  LatLng centerPosition;
  InfoWindow infoWindow =
  InfoWindow(title: "Location");
  String _locationMessage = "";
  double mylat, mylon, pilat, pilon, dist;
  Marker predog;
  LatLng predest, presource;

  void _onMapCreated(GoogleMapController controller) {
    _controller.complete(controller);
  }

  void _onMapTypeButtonPressed() {
    setState(() {
      _currentMapType = _currentMapType == MapType.normal
          ? MapType.satellite
          : MapType.normal;
      print(_currentMapType.toString());
    });
  }

  /*void _onAddMarkerButtonPressed() async{
    setState(() {
    });
  }*/

  @override
  void initState(){ // listening raspberry's location
    super.initState();
    
    fireBaseDBSubScription = fireBaseDB.child("gpsData").onValue.listen((Event event){
      if(event.snapshot.value!=null){
        Map map = event.snapshot.value;
        this.setState(() {
          pilat = map['lat'];
          pilon = map['lon'];
          Marker dog = Marker(
            markerId: MarkerId(markers.length.toString()),
            infoWindow: infoWindow,
            position: LatLng(pilat, pilon),
            icon: pinLocationIcon,
            //icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed),
          );
          markers.add(dog);
          markers.remove(predog);
          //sd.remove(predest);
          //sd.add(LatLng(pilat, pilon));
          predog = dog;
          //predest = LatLng(pilat, pilon);
        });
        _getCurrentLocation();
      }
      /*sd.add(LatLng(24.9670568, 121.1869849));
      sd.add(LatLng(24.9680568, 121.1969849));*/
    });
    BitmapDescriptor.fromAssetImage(
         ImageConfiguration(devicePixelRatio: 2.5),
         'assets/dog144.png').then((onValue) {
            pinLocationIcon = onValue;
         });
  }

  void _getCurrentLocation() async {
    final position = await Geolocator().getCurrentPosition(desiredAccuracy: LocationAccuracy.high);
    //print(position);
    setState(() {
      _locationMessage = "${position.latitude}, ${position.longitude}";
      mylat = double.parse("${position.latitude}");
      mylon = double.parse("${position.longitude}");
      /*Marker person = Marker(
        markerId: MarkerId(markers.length.toString()),
        infoWindow: infoWindow,
        position: LatLng(mylat, mylon),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
      );
      print(markers.length);
      markers.add(person);
      markers.remove(preperson);
      //sd.remove(presource);
      //sd.add(centerPosition);
      preperson = person;
      //presource = centerPosition;
      print(markers.length);*/
      _set();
    });
  }

  double _getDistance(){
    double p = 0.017453292519943295;
    double temp = 0.5 - cos((pilat - mylat) * p)/2 + cos(mylat * p) * cos(pilat * p) * 
          (1 - cos((pilon - mylon) * p))/2;
    return 12742 * asin(sqrt(temp));
  }
  @override
  void dispose(){
    super.dispose();
    fireBaseDBSubScription.cancel();
  }

  void _set(){
    Map<String,double> data = {
      "lat":mylat,
      "lon":mylon
    };
    fireBaseDB.child("location").set(data).whenComplete((){
      print("finish set location");
    }).catchError((error){
      print(error);
    });
    fireBaseDB.child("distance").set(_getDistance()).whenComplete((){
      print("finish set distance");
    }).catchError((error){
      print(error);
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: new ThemeData(
        primaryColor: const Color(0xFF02BB9F),
        primaryColorDark: const Color(0xFF167F67),
        accentColor: const Color(0xFF02BB9F),
      ),
      home: Scaffold(
        appBar: AppBar(
          title: Text(
            'Fing My Dog',
            style: TextStyle(color: Colors.white),
          ),
        ),
        body: Stack(
          children: <Widget>[
            GoogleMap(
              onMapCreated: _onMapCreated,
              mapType: _currentMapType,
              myLocationEnabled: true,
              markers: markers,
              onCameraMove: _onCameraMove,
              initialCameraPosition: CameraPosition(
                target: _center,
                zoom: 17.0,
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Align(
                alignment: Alignment.bottomLeft,
                child: new FloatingActionButton(
                  onPressed: _onMapTypeButtonPressed,
                  child: new Icon(
                    Icons.map,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
            /*Padding(
              padding: const EdgeInsets.all(16.0),
              child: Align(
                alignment: Alignment.bottomCenter,
                child: new FloatingActionButton(
                  onPressed: _onAddMarkerButtonPressed,
                  child: new Icon(
                    Icons.edit_location,
                    color: Colors.white,
                  ),
                ),
              ),
            ),*/
          ],
        ),
      ),
    );
    
  }

  void _onCameraMove(CameraPosition position) {
    centerPosition = position.target;
  }
}