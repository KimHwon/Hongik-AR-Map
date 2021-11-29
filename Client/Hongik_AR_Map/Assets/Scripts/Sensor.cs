using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System;
using System.Text;

public class Sensor : MonoBehaviour
{
    public static double latitude;
    public static double longitude;
    public static double altitude;
    public static bool gpsStarted = false;
    private static LocationInfo location;
    private static WaitForSeconds second;

    Socket data_sock = null;
    string IP = null;
    enum DataFormat : byte
    {
        EMPTY = 0x00,
        TEXT = 0x01,
        SENSOR = 0x02,
        DEST = 0x03
    };
    const byte ETX = 0x03;

    byte[] buffer = new byte[1024];

    private void Awake()
    {
        second = new WaitForSeconds(1.0f);
        IP = Loading.Instance.GetIP();
        data_sock = Loading.Instance.GetDatatSocket();
    }

    // Start is called before the first frame update
    IEnumerator Start()
    {
        if (!Input.location.isEnabledByUser)
        {
            SetText("loc", "GPS is not enabled");
            yield break;
        }

        Input.location.Start(.5f, .5f);
        SetText("loc", "Awaiting initialization");

        int maxWait = 10;
        while (Input.location.status == LocationServiceStatus.Initializing && maxWait > 0)
        {
            yield return second;
            maxWait--;
        }

        if (maxWait < 1)
        {
            SetText("loc", "Timed out");
            yield break;
        }

        if (Input.location.status == LocationServiceStatus.Failed)
        {
            SetText("loc", "Unable to determine device location");
            yield break;
        }
        SetText("loc", "ok");
        gpsStarted = true;

        while (gpsStarted)
        {
            int i;
            for (i = 0; i < buffer.Length; i++) buffer[i] = (byte)DataFormat.EMPTY;
            location = Input.location.lastData;
            latitude = location.latitude * 1.0d;
            longitude = location.longitude * 1.0d;
            altitude = location.altitude * 1.0d;
            
            byte[] msg = Encoding.UTF8.GetBytes("save");
            buffer[0] = (byte)DataFormat.SENSOR;
            for (i = 0; i < Math.Min(buffer.Length - 2, msg.Length); i++)
                buffer[i + 1] = msg[i];
            buffer[i + 1] = ETX;

            data_sock.Send(buffer, 1024, SocketFlags.None); // Client must send first.

            data_sock.Receive(buffer, 1024, SocketFlags.None);
            // do something with `buffer`.
            yield return second;
        }
    }

    // Update is called once per frame
    void Update()
    {

    }

    public static void StopGPS()
    {
        if (Input.location.isEnabledByUser)
        {
            gpsStarted = false;
            Input.location.Stop();
        }
    }

    void SetText(string name, string str)
    {
        GameObject debugText = GameObject.Find(name);
        if (debugText != null)
        {
            TextMesh textMesh = debugText.GetComponent("TextMesh") as TextMesh;
            if (textMesh != null)
            {
                textMesh.text = str;
            }
        }
    }
}
