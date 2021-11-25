using System.Collections;
using System.Collections.Generic;
using UnityEngine;

using System;
using System.Net;
using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.IO;
using System.Text;

public class Cam : MonoBehaviour
{
    WebCamTexture webCamTexture = null;
    Socket image_sock = null;
    Socket data_sock = null;

    string IP = "192.168.0.100";

    enum DataFormat : byte
    {
        EMPTY   = 0x00,
        TEXT    = 0x01,
        SENSOR  = 0x02,
        DEST    = 0x03
    };
    const byte ETX = 0x03;

    byte[] buffer = new byte[1024];

    LocationInfo location;
    AndroidJavaObject plugin;
    
    // Start is called before the first frame update
    void Start()
    {
        webCamTexture = new WebCamTexture();
        GetComponent<Renderer>().material.mainTexture = webCamTexture; //Add Mesh Renderer to the GameObject to which this script is attached to
        webCamTexture.Play();

        string configPath = Application.persistentDataPath + "/config.txt";
        if (File.Exists(configPath))
        {
            StreamReader reader = new StreamReader(configPath);
            string data = reader.ReadToEnd();
            IP = data;
            reader.Close();
        }
        else
        {
            StreamWriter writer = new StreamWriter(configPath);
            string data = IP;
            writer.Write(data);
            writer.Close();
        }
        SetText("DebugText", IP);

        image_sock = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
        IPEndPoint ep1 = new IPEndPoint(IPAddress.Parse(IP), 50020);
        image_sock.Connect(ep1);

        data_sock = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
        IPEndPoint ep2 = new IPEndPoint(IPAddress.Parse(IP), 50021);
        data_sock.Connect(ep2);

        StartCoroutine("TakePhoto");


        //GPS
        UnityEngine.Android.Permission.RequestUserPermission("android.permission.ACCESS_FINE_LOCATION");
        //외부 저장소
        UnityEngine.Android.Permission.RequestUserPermission(UnityEngine.Android.Permission.ExternalStorageWrite);
        Input.location.Start(0.5f);

    }

    // Update is called once per frame
    void Update()
    {
        for (int i = 0; i < buffer.Length; i++) buffer[i] = (byte)DataFormat.EMPTY;
        if (Input.touchCount > 0)
        {
            int i;
            byte[] msg = Encoding.UTF8.GetBytes("save");
            buffer[0] = (byte)DataFormat.TEXT;
            for (i = 0; i < Math.Min(buffer.Length-2, msg.Length); i++)
                buffer[i+1] = msg[i];
            buffer[i+1] = ETX;
        }
        if (Input.GetKeyDown(KeyCode.Escape))
        {
            Application.Quit();
        }
        data_sock.Send(buffer, 1024, SocketFlags.None); // Client must send first.

        
        data_sock.Receive(buffer, 1024, SocketFlags.None);
        // do something with `buffer`.


        if (!Input.location.isEnabledByUser)
        {
            SetText("DebugText", "Disabled");
        }
        else if (Input.location.status == LocationServiceStatus.Initializing)
        {
            SetText("DebugText", "Init");
        }
        else if (Input.location.status == LocationServiceStatus.Failed)
        {
            SetText("DebugText", "Failed");
        }
        else
        {
            location = Input.location.lastData;
            float Lat = location.latitude;
            float Long = location.longitude;
            SetText("DebugText", Lat.ToString() + ", " + Long.ToString());
        }

    }

    void OnApplicationQuit()
    {
        if (image_sock != null) image_sock.Close();
        if (data_sock != null)
        {
            int i;
            byte[] msg = Encoding.UTF8.GetBytes("exit");
            buffer[0] = (byte)DataFormat.TEXT;
            for (i = 0; i < Math.Min(buffer.Length-2, msg.Length); i++)
                buffer[i+1] = msg[i];
            buffer[i+1] = ETX;

            data_sock.Send(buffer, 1024, SocketFlags.None);
            data_sock.Close();
        }


    }

    IEnumerator TakePhoto()
    {
        while (true) {
            yield return new WaitForSeconds(.5f);
            // NOTE - you almost certainly have to do this here:
            yield return new WaitForEndOfFrame(); 

            // it's a rare case where the Unity doco is pretty clear,
            // http://docs.unity3d.com/ScriptReference/WaitForEndOfFrame.html
            // be sure to scroll down to the SECOND long example on that doco page 

            Texture2D photo = new Texture2D(webCamTexture.width, webCamTexture.height);
            photo.SetPixels(webCamTexture.GetPixels());
            photo.Apply();

            try
            {
                //Encode to a JPG
                byte[] bytes = photo.EncodeToJPG();

                //SetText("DebugText", bytes.Length.ToString());

                image_sock.Send(bytes, SocketFlags.None);
            }
            catch (Exception e)
            {
                SetText("DebugText", e.ToString());
            }
        }
    }

    void SetText(string name, string str) {
        GameObject debugText = GameObject.Find(name);
        if (debugText != null) {
            TextMesh textMesh = debugText.GetComponent("TextMesh") as TextMesh;
            if (textMesh != null) {
                textMesh.text = str;
            }
        }
    }
}