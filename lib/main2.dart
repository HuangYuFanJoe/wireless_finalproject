import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:firebase_database/firebase_database.dart';
import 'dart:async';
import 'package:google_maps_flutter/google_maps_flutter.dart';

void main() => runApp(MyApp());

class MyApp extends StatefulWidget {
  @override
  _AppState createState() => _AppState();
}

class _AppState extends State<MyApp> {
  final DatabaseReference fireBaseDB = FirebaseDatabase.instance.reference();
  StreamSubscription<Event> fireBaseDBSubScription;
  String _locationMessage = "";
  double mylat;
  double mylon;
  double pilat;
  double pilon;
  String spilat = "";
  String spilon = "";
  String _sendMessage = "";

  void _getCurrentLocation() async {
    final position = await Geolocator().getCurrentPosition(desiredAccuracy: LocationAccuracy.high);
    print(position);

    setState(() {
      _locationMessage = "${position.latitude}, ${position.longitude}";
      mylat = double.parse("${position.latitude}");
      mylon = double.parse("${position.longitude}");
    });
  }

  @override
  void initState(){ // listening raspberry's location
    super.initState();
    fireBaseDBSubScription = fireBaseDB.child("gpsData").onValue.listen((Event event){
      if(event.snapshot.value!=null){
        Map map = event.snapshot.value;
        this.setState(() {
          pilat = map['lat'];
          pilon = map['lon'];
          spilat = pilat.toString();
          spilon = pilon.toString();
        });
      }
    });
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
      print("finish set");
    }).catchError((error){
      print(error);
    });
  }
  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Demo',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: Scaffold(
        appBar: AppBar(
          title: Text("Flutter demo"),
        ),
        body: Align(
            child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
            Text("My dog's location:" ,style: TextStyle(fontSize: 30, color: Colors.blue[300])),
            Text(spilat + ", " + spilon + "\n\n\n" ,style: TextStyle(fontSize: 30, color: Colors.grey[500])),
            Text("My location:" ,style: TextStyle(fontSize: 30, color: Colors.blue[300])),
            Text( _locationMessage ,style: TextStyle(fontSize: 30, color: Colors.grey[500])),
            FlatButton(
                onPressed: () {
                    _getCurrentLocation();
                },
                color: Colors.green,
                child: Text("Find my location")
            ),
            FlatButton(
                onPressed: () {
                   _set(); 
                },
                color: Colors.grey,
                child: Text("Send to firebase")
            ),
            RaisedButton(
              textColor: Colors.white,
              color: Colors.blue,
              child: Text('Go to MyHomePage'),
              onPressed: () {
                //navigateToMyHomePage(context);
                Navigator.push(context, MaterialPageRoute(builder: (context) => MyHomePage()));
              },
            ),
            Text(_sendMessage)
            ]),
        ),
      
      )
    );
  }
  Future navigateToMyHomePage(context) async {
    Navigator.push(context, MaterialPageRoute(builder: (context) => MyHomePage()));
  }
}

class MyHomePage extends StatefulWidget {
  MyHomePage({Key key, this.title, AppBar appBar, Align body}) : super(key: key);


  final String title;

  @override
  _MyHomePageState createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
@override
Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Sub Page'),
        backgroundColor: Colors.redAccent,
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Text('Click button to back to Main Page'),
            RaisedButton(
              textColor: Colors.white,
              color: Colors.redAccent,
              child: Text('Back to Main Page'),
              onPressed: () {
                backToMainPage(context);
              },
            )
          ],
        ),
      ),
    );
}

  void backToMainPage(context) {
    Navigator.pop(context);
  }
  /*@override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
          ],
        ),
      ),
    );
  }*/
}
